from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Application,
    Certification,
    Company,
    Education,
    Experience,
    Job,
    JobSeekerProfile,
    Project,
    Resume,
    Skill,
    User,
    UserSkill,
)
from app.recommendation import (
    ProfileView,
    build_insights,
    build_job_skill_roadmap,
    estimate_experience_years,
    find_career_for_title,
    generate_recommendations,
    score_job,
)
from app.routers.auth import get_current_user
from app.skills import extract_skills_from_text, split_skill_list

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class RoadmapQuery(BaseModel):
    job_id: Optional[int] = None
    target_role: Optional[str] = None
    required_skills: Optional[str] = None


def _strength(proficiency: int | None) -> float:
    """Proficiency 1..5 -> 0.6..1.0 so a beginner-level skill still counts, but less."""
    level = min(5, max(1, int(proficiency or 3)))
    return 0.6 + 0.1 * (level - 1)


def load_profile(user_id: int, db: Session) -> dict:
    """Collect everything we know about a job seeker into the engine's profile dict."""
    skill_levels: dict[str, float] = {}

    def bump(name: str, strength: float) -> None:
        if name and name.strip():
            skill_levels[name.strip()] = max(skill_levels.get(name.strip(), 0.0), strength)

    rows = (
        db.query(Skill.name, UserSkill.proficiency)
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == user_id)
        .all()
    )
    for name, proficiency in rows:
        bump(name, _strength(proficiency))

    record = db.query(JobSeekerProfile).filter(JobSeekerProfile.user_id == user_id).first()
    summary_skills = split_skill_list(record.skills_summary) if record and record.skills_summary else []

    resume_skills: list[str] = []
    for resume in db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.uploaded_at.desc()).all():
        for skill in split_skill_list(resume.extracted_skills):
            if skill not in resume_skills:
                resume_skills.append(skill)

    project_skills: list[str] = []
    for project in db.query(Project).filter(Project.user_id == user_id).all():
        project_skills.extend(split_skill_list(project.technologies))
        project_skills.extend(extract_skills_from_text(f"{project.title or ''} {project.description or ''}"))

    experiences = db.query(Experience).filter(Experience.user_id == user_id).all()
    experience_text = " ".join(f"{e.title or ''} {e.description or ''}" for e in experiences)
    for skill in extract_skills_from_text(experience_text):
        bump(skill, 0.75)

    certifications = [c.name for c in db.query(Certification).filter(Certification.user_id == user_id).all() if c.name]
    for skill in extract_skills_from_text(" ".join(certifications)):
        bump(skill, 0.7)

    education_rows = db.query(Education).filter(Education.user_id == user_id).all()
    education_text = " ".join(
        [record.education_level or "" if record else ""]
        + [f"{e.degree or ''} {e.field or ''}" for e in education_rows]
    ).strip()

    return {
        "skills": summary_skills,
        "skill_levels": skill_levels,
        "resume_skills": resume_skills,
        "project_skills": project_skills,
        "certifications": certifications,
        "education_level": record.education_level if record else "",
        "education_text": education_text,
        "career_interest": (record.career_goals or "") if record else "",
        "experience_years": estimate_experience_years((e.start_date, e.end_date) for e in experiences),
        "experience_text": experience_text,
        "work_mode": record.work_mode if record else "",
        "preferred_location": record.preferred_location if record else "",
    }


def _empty_insights() -> dict:
    return {"best_fit": None, "best_fit_score": None, "top_skills_to_learn": [], "profile_strength": {"score": 0, "label": "Low", "tips": []}}


@router.get("")
def get_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "job_seeker":
        return []
    return generate_recommendations(load_profile(current_user.id, db))


@router.get("/insights")
def get_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Highest-impact skills to learn next across the user's best-matching careers."""
    if current_user.role != "job_seeker":
        return _empty_insights()
    profile = load_profile(current_user.id, db)
    return build_insights(profile, generate_recommendations(profile))


@router.get("/jobs")
def get_recommended_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rank active jobs for the user: skills (with partial credit), goal fit, experience, preferences."""
    if current_user.role != "job_seeker":
        return []

    profile_data = load_profile(current_user.id, db)
    profile = ProfileView(profile_data)
    career_scores = {c["title"]: c["score"] for c in generate_recommendations(profile_data)}
    applied_job_ids = {
        job_id for (job_id,) in db.query(Application.job_id).filter(Application.user_id == current_user.id).all()
    }
    company_names = {cid: name for cid, name in db.query(Company.id, Company.name).all()}

    results = []
    for job in db.query(Job).filter(Job.is_active.is_(True)).all():
        scored = score_job(
            {
                "title": job.title,
                "required_skills": job.required_skills,
                "preferred_qualifications": job.preferred_qualifications,
                "experience": job.experience,
                "work_mode": job.work_mode,
                "location": job.location,
            },
            profile,
            career_scores,
        )
        results.append(
            {
                "job_id": job.id,
                "title": job.title,
                "company": company_names.get(job.company_id, ""),
                "location": job.location,
                "salary_range": job.salary_range,
                "employment_type": job.employment_type,
                "work_mode": job.work_mode,
                "experience": job.experience,
                "description": job.description,
                "already_applied": job.id in applied_job_ids,
                **scored,
            }
        )

    results.sort(key=lambda item: (item["already_applied"], -item["match_score"], item["title"]))
    return results


@router.post("/roadmap")
def get_custom_roadmap(
    payload: RoadmapQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Required skills + a personalised step-by-step roadmap for any job or career goal."""
    profile = ProfileView(load_profile(current_user.id, db))

    job_title = (payload.target_role or "").strip() or "Target Job"
    required_skills = (payload.required_skills or "").strip()

    if payload.job_id:
        job = db.query(Job).filter(Job.id == payload.job_id).first()
        if job:
            job_title = job.title
            required_skills = job.required_skills or ""

    if not required_skills:
        career = find_career_for_title(job_title)
        if career:
            required_skills = ", ".join(career["required_skills"] + career["recommended_skills"])

    if not required_skills:
        required_skills = "Problem Solving, Core Domain Knowledge, Technical Tools, Collaboration"

    return build_job_skill_roadmap(job_title=job_title, required_skills=required_skills, profile=profile)
