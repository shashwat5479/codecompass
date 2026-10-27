from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Application, ApplicationStatusHistory, Job, Company, RecruiterProfile, Resume
from app.routers.auth import get_current_user
from app.schemas import ApplicationCreate

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("")
def list_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "job_seeker":
        raise HTTPException(status_code=403, detail="Only job seekers can view their applications")
    rows = (
        db.query(Application, Job.title)
        .join(Job, Application.job_id == Job.id)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.submitted_at.desc())
        .all()
    )
    return [
        {
            "id": application.id,
            "job_id": application.job_id,
            "job_title": title,
            "status": application.status,
            "submitted_at": application.submitted_at,
        }
        for application, title in rows
    ]


@router.get("/recruiter")
def recruiter_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Recruiter access required")
    recruiter = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == current_user.id).first()
    if not recruiter:
        return []
    rows = (
        db.query(Application, User, Job)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .join(User, Application.user_id == User.id)
        .filter(Company.name == recruiter.company_name)
        .order_by(Application.submitted_at.desc())
        .all()
    )
    return [
        {
            "id": application.id,
            "job_id": job.id,
            "job_title": job.title,
            "applicant_name": applicant.full_name,
            "applicant_email": applicant.email,
            "status": application.status,
            "submitted_at": application.submitted_at,
            "cover_letter": application.cover_letter,
            "notes": application.notes,
        }
        for application, applicant, job in rows
    ]


@router.post("")
def apply(payload: ApplicationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "job_seeker":
        raise HTTPException(status_code=403, detail="Only job seekers can apply to jobs")
    job = db.query(Job).filter(Job.id == payload.job_id, Job.is_active.is_(True)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if payload.resume_id is not None and not db.query(Resume).filter(
        Resume.id == payload.resume_id,
        Resume.user_id == current_user.id,
    ).first():
        raise HTTPException(status_code=404, detail="Resume not found")
    existing = db.query(Application).filter(Application.user_id == current_user.id, Application.job_id == payload.job_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already applied to this job")

    # Combine application details cleanly into notes
    details = []
    if payload.full_name:
        details.append(f"Applicant Name: {payload.full_name}")
    if payload.phone:
        details.append(f"Phone: {payload.phone}")
    if payload.experience:
        details.append(f"Experience: {payload.experience}")
    if payload.education:
        details.append(f"Education: {payload.education}")
    if payload.skills:
        details.append(f"Key Skills: {payload.skills}")
    if payload.portfolio_url:
        details.append(f"Portfolio / Links: {payload.portfolio_url}")
    if payload.notice_period:
        details.append(f"Notice Period: {payload.notice_period}")
    if payload.notes:
        details.append(payload.notes)

    final_notes = " | ".join(details) if details else payload.notes

    app = Application(
        user_id=current_user.id,
        job_id=payload.job_id,
        resume_id=payload.resume_id,
        cover_letter=payload.cover_letter,
        notes=final_notes,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    db.add(ApplicationStatusHistory(application_id=app.id, old_status=None, new_status="Applied"))
    db.commit()
    return {"message": "Application submitted successfully", "application_id": app.id}


@router.get("/{application_id}")
def get_application(application_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return app


@router.patch("/{application_id}/status")
def update_status(application_id: int, payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if current_user.role not in ("admin", "recruiter"):
        raise HTTPException(status_code=403, detail="Not authorized")
    new_status = payload.get("status")
    allowed_statuses = {"Applied", "Reviewing", "Shortlisted", "Interview", "Rejected", "Hired"}
    if new_status not in allowed_statuses:
        raise HTTPException(status_code=422, detail="Invalid application status")
    if current_user.role == "recruiter":
        recruiter = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == current_user.id).first()
        owned = (
            db.query(Application.id)
            .join(Job, Application.job_id == Job.id)
            .join(Company, Job.company_id == Company.id)
            .filter(Application.id == application_id, Company.name == (recruiter.company_name if recruiter else ""))
            .first()
        )
        if not owned:
            raise HTTPException(status_code=403, detail="You cannot update applications for another company")
    old = app.status
    app.status = new_status
    app.updated_at = __import__("datetime").datetime.utcnow()
    db.add(ApplicationStatusHistory(application_id=app.id, old_status=old, new_status=app.status))
    db.commit()
    return {"message": "Status updated"}
