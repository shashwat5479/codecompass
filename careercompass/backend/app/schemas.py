from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str
    role: str = "job_seeker"
    education_level: Optional[str] = None
    phone_number: Optional[str] = None
    recruiter_name: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_description: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    education_level: Optional[str] = None
    phone_number: Optional[str] = None
    preferred_location: Optional[str] = None
    work_mode: Optional[str] = None
    salary_expectation: Optional[str] = None
    career_goals: Optional[str] = None
    skills_summary: Optional[str] = None


class SkillInput(BaseModel):
    name: str
    proficiency: int = Field(default=1, ge=1, le=5)


class JobCreate(BaseModel):
    title: str
    company_id: int
    description: str
    responsibilities: str
    required_skills: str
    preferred_qualifications: str
    education: str = "Bachelor's degree"
    experience: str = "0-2 years"
    employment_type: str = "Full-time"
    salary_range: str = "Not disclosed"
    location: str = "Remote"
    work_mode: str = "remote"
    deadline: Optional[str] = None
    openings: int = 1
    is_active: bool = True


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: Optional[int] = None
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None
    portfolio_url: Optional[str] = None
    notice_period: Optional[str] = None


class PostCreate(BaseModel):
    title: str
    content: str
    category: str = "General Discussion"
    tags: str = ""


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None
