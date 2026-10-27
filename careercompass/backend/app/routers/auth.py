from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, JobSeekerProfile, RecruiterProfile, Company
from app.schemas import LoginRequest, UserCreate
from app.config import settings
from passlib.context import CryptContext

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(email: str) -> str:
    expires_at = int(time.time()) + 60 * 60 * 24
    payload = base64.urlsafe_b64encode(f"{email}|{expires_at}".encode()).decode().rstrip("=")
    signature = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload, signature = token.split(".", 1)
        expected_signature = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")
        decoded_payload = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode()
        email, expires_at = decoded_payload.rsplit("|", 1)
        if int(expires_at) <= int(time.time()):
            raise ValueError("Token expired")
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if user_data.role not in {"job_seeker", "recruiter"}:
        raise HTTPException(status_code=400, detail="Registration is available for job seekers and recruiters only")
    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=user_data.full_name,
        email=str(user_data.email),
        password_hash=get_password_hash(user_data.password),
        role=user_data.role or "job_seeker",
        is_active=True,
    )
    db.add(user)
    db.flush()

    if user_data.role == "recruiter":
        company_name = (user_data.company_name or "").strip()
        if not company_name:
            db.rollback()
            raise HTTPException(status_code=400, detail="Company name is required for recruiter registration")
        if db.query(Company).filter(Company.name.ilike(company_name)).first():
            db.rollback()
            raise HTTPException(status_code=409, detail="This company is already registered. Contact an administrator to link your account.")
        company = Company(
            name=company_name,
            website=user_data.company_website,
            description=user_data.company_description,
            industry=user_data.industry,
            is_verified=False,
        )
        db.add(company)
        recruiter = RecruiterProfile(
            user_id=user.id,
            recruiter_name=user_data.recruiter_name or user_data.full_name,
            company_name=company_name,
            company_website=user_data.company_website,
            company_description=user_data.company_description,
            industry=user_data.industry,
            company_size=user_data.company_size,
            verification_status="pending",
        )
        db.add(recruiter)
    else:
        seeker = JobSeekerProfile(
            user_id=user.id,
            education_level=user_data.education_level,
            phone_number=user_data.phone_number,
            profile_completion=10,
        )
        db.add(seeker)
    db.commit()
    return {"message": "User registered successfully", "role": user.role}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.email)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "name": user.full_name, "email": user.email, "role": user.role}}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.full_name, "email": current_user.email, "role": current_user.role}


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
