from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Company, Job, SavedJob, JobSkill, RecruiterProfile
from app.routers.auth import get_current_user
from app.schemas import JobCreate

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/company")
def recruiter_company(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Recruiter access required")
    recruiter = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == current_user.id).first()
    company = db.query(Company).filter(
        Company.name == (recruiter.company_name if recruiter else ""),
        Company.is_verified.is_(True),
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="No verified company is linked to this recruiter")
    return {"id": company.id, "name": company.name}


@router.get("")
def list_jobs(db: Session = Depends(get_db), q: str | None = None):
    jobs = db.query(Job).filter(Job.is_active.is_(True)).all()
    result = []
    for job in jobs:
        company = db.query(Company).filter(Company.id == job.company_id).first()
        result.append({
            "id": job.id,
            "title": job.title,
            "company": company.name if company else "Unknown",
            "location": job.location,
            "salary_range": job.salary_range,
            "employment_type": job.employment_type,
            "experience": job.experience,
            "description": job.description,
            "required_skills": job.required_skills,
            "work_mode": job.work_mode,
            "is_active": job.is_active,
        })
    if q:
        term = q.casefold()
        result = [
            job for job in result
            if any(term in str(job.get(field) or "").casefold() for field in ("title", "description", "required_skills", "company"))
        ]
    return result


@router.get("/{job_id:int}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.is_active.is_(True)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    company = db.query(Company).filter(Company.id == job.company_id).first()
    return {"job": job, "company": company}


@router.post("")
def create_job(payload: JobCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can create jobs")
    recruiter = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == current_user.id).first()
    company = db.query(Company).filter(
        Company.id == payload.company_id,
        Company.name == (recruiter.company_name if recruiter else ""),
        Company.is_verified.is_(True),
    ).first()
    if not company:
        raise HTTPException(status_code=403, detail="A verified company profile is required to post jobs")
    job = Job(
        company_id=company.id,
        title=payload.title,
        description=payload.description,
        responsibilities=payload.responsibilities,
        required_skills=payload.required_skills,
        preferred_qualifications=payload.preferred_qualifications,
        education=payload.education,
        experience=payload.experience,
        employment_type=payload.employment_type,
        salary_range=payload.salary_range,
        location=payload.location,
        work_mode=payload.work_mode,
        deadline=payload.deadline,
        openings=payload.openings,
        is_active=payload.is_active,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    for skill in [s.strip() for s in payload.required_skills.split(',') if s.strip()]:
        db.add(JobSkill(job_id=job.id, skill_name=skill))
    db.commit()
    return {"message": "Job created", "job_id": job.id}


@router.post("/{job_id}/save")
def save_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "job_seeker":
        raise HTTPException(status_code=403, detail="Only job seekers can save jobs")
    job = db.query(Job).filter(Job.id == job_id, Job.is_active.is_(True)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = db.query(SavedJob).filter(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id).first()
    if existing:
        return {"message": "Already saved"}
    db.add(SavedJob(user_id=current_user.id, job_id=job_id))
    db.commit()
    return {"message": "Job saved"}


@router.get("/saved")
def saved_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
    return [{"job_id": row.job_id} for row in rows]


@router.get("/mine")
def recruiter_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can view their company jobs")
    recruiter = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == current_user.id).first()
    if not recruiter:
        return []
    return db.query(Job).join(Company, Job.company_id == Company.id).filter(
        Company.name == recruiter.company_name,
    ).order_by(Job.created_at.desc()).all()
