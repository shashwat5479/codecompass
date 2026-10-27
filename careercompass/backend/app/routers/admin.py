from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Company, CommunityPost, Job, Application, RecruiterProfile
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "total_users": db.query(User).count(),
        "total_jobs": db.query(Job).count(),
        "total_posts": db.query(CommunityPost).count(),
        "verified_companies": db.query(Company).filter(Company.is_verified.is_(True)).count(),
    }


@router.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in {"admin", "recruiter"}:
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.role == "recruiter":
        recruiter = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == current_user.id).first()
        company_jobs = db.query(Job.id).join(Company, Job.company_id == Company.id).filter(
            Company.name == (recruiter.company_name if recruiter else ""),
        )
        job_ids = [job_id for (job_id,) in company_jobs.all()]
        applications = db.query(Application).filter(Application.job_id.in_(job_ids))
        return {
            "role": "recruiter",
            "active_roles": db.query(Job).filter(Job.id.in_(job_ids), Job.is_active.is_(True)).count(),
            "qualified_applicants": applications.filter(Application.status.in_(["Applied", "Reviewing", "Shortlisted", "Interview"])).count(),
            "interviews": applications.filter(Application.status == "Interview").count(),
        }

    return {
        "role": "admin",
        "total_users": db.query(User).count(),
        "active_jobs": db.query(Job).filter(Job.is_active.is_(True)).count(),
        "verified_companies": db.query(Company).filter(Company.is_verified.is_(True)).count(),
        "total_posts": db.query(CommunityPost).count(),
        "pending_companies": db.query(Company).filter(Company.is_verified.is_(False)).count(),
    }


@router.get("/companies/pending")
def pending_companies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    companies = db.query(Company).filter(Company.is_verified.is_(False)).order_by(Company.created_at.asc()).all()
    return [
        {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "industry": company.industry,
            "description": company.description,
        }
        for company in companies
    ]


@router.patch("/companies/{company_id}/verify")
def verify_company(company_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.is_verified = True
    db.query(RecruiterProfile).filter(RecruiterProfile.company_name == company.name).update(
        {RecruiterProfile.verification_status: "verified"},
        synchronize_session=False,
    )
    db.commit()
    return {"message": "Company verified", "company_id": company.id}
