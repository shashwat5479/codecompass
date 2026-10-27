from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, JobSeekerProfile, Experience, Education, Project, Certification, Skill, UserSkill
from app.routers.auth import get_current_user
from app.schemas import ProfileUpdate, SkillInput

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(JobSeekerProfile).filter(JobSeekerProfile.user_id == current_user.id).first()
    return {
        "user": {"id": current_user.id, "full_name": current_user.full_name, "email": current_user.email, "role": current_user.role},
        "profile": profile,
    }


@router.put("/me")
def update_profile(payload: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(JobSeekerProfile).filter(JobSeekerProfile.user_id == current_user.id).first()
    if not profile:
        profile = JobSeekerProfile(user_id=current_user.id)
        db.add(profile)
    updates = payload.model_dump(exclude_unset=True)
    full_name = updates.pop("full_name", None)
    if full_name:
        current_user.full_name = full_name
    for field, value in updates.items():
        if value is not None:
            setattr(profile, field, value)
    completion_fields = (
        profile.education_level,
        profile.phone_number,
        profile.preferred_location,
        profile.work_mode,
        profile.salary_expectation,
        profile.career_goals,
        profile.skills_summary,
    )
    profile.profile_completion = round(100 * sum(bool(value and value.strip()) for value in completion_fields) / len(completion_fields))
    db.commit()
    return {"message": "Profile updated", "profile_completion": profile.profile_completion}


@router.post("/skills")
def add_skill(payload: SkillInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    skill = db.query(Skill).filter(Skill.name.ilike(payload.name)).first()
    if not skill:
        skill = Skill(name=payload.name)
        db.add(skill)
        db.flush()
    record = UserSkill(user_id=current_user.id, skill_id=skill.id, proficiency=payload.proficiency)
    db.add(record)
    db.commit()
    return {"message": "Skill added"}


@router.get("/skills")
def list_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    result = []
    for item in records:
        skill = db.query(Skill).filter(Skill.id == item.skill_id).first()
        result.append({"id": item.id, "name": skill.name if skill else "Unknown", "proficiency": item.proficiency})
    return result


@router.post("/education")
def add_education(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = Education(user_id=current_user.id, **payload)
    db.add(item)
    db.commit()
    return {"message": "Education added"}


@router.post("/experience")
def add_experience(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = Experience(user_id=current_user.id, **payload)
    db.add(item)
    db.commit()
    return {"message": "Experience added"}


@router.post("/projects")
def add_project(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = Project(user_id=current_user.id, **payload)
    db.add(item)
    db.commit()
    return {"message": "Project added"}


@router.post("/certifications")
def add_certification(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = Certification(user_id=current_user.id, **payload)
    db.add(item)
    db.commit()
    return {"message": "Certification added"}
