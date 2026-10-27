from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def register_user(
    client: TestClient,
    *,
    full_name: str,
    email: str,
    password: str,
    role: str,
    **details: str,
) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "confirm_password": password,
            "role": role,
            **details,
        },
    )
    assert response.status_code == 200, response.text


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_recruiter_verification_to_job_application_lifecycle(client: TestClient) -> None:
    register_user(
        client,
        full_name="Riley Recruiter",
        email="recruiter@example.com",
        password="recruiter-password",
        role="recruiter",
        company_name="Test Company",
    )
    register_user(
        client,
        full_name="Sam Seeker",
        email="seeker@example.com",
        password="seeker-password",
        role="job_seeker",
    )

    recruiter_headers = login(client, "recruiter@example.com", "recruiter-password")
    seeker_headers = login(client, "seeker@example.com", "seeker-password")
    admin_headers = login(client, "admin@example.com", "admin-password")

    pending = client.get("/api/admin/companies/pending", headers=admin_headers)
    assert pending.status_code == 200
    company = next(item for item in pending.json() if item["name"] == "Test Company")
    assert client.get("/api/jobs/company", headers=recruiter_headers).status_code == 404

    posted_before_verification = client.post(
        "/api/jobs",
        headers=recruiter_headers,
        json={
            "title": "Software Engineer",
            "company_id": company["id"],
            "description": "Build reliable software",
            "responsibilities": "Develop and maintain services",
            "required_skills": "Python, SQL",
        },
    )
    assert posted_before_verification.status_code == 403

    verified = client.patch(
        f"/api/admin/companies/{company['id']}/verify",
        headers=admin_headers,
    )
    assert verified.status_code == 200
    assert client.get("/api/jobs/company", headers=recruiter_headers).json()["name"] == "Test Company"

    created = client.post(
        "/api/jobs",
        headers=recruiter_headers,
        json={
            "title": "Software Engineer",
            "company_id": company["id"],
            "description": "Build reliable software",
            "responsibilities": "Develop and maintain services",
            "required_skills": "Python, SQL",
        },
    )
    assert created.status_code == 200, created.text
    job_id = created.json()["job_id"]

    search = client.get("/api/jobs", params={"q": "python"})
    assert search.status_code == 200
    assert any(job["id"] == job_id for job in search.json())

    saved = client.post(f"/api/jobs/{job_id}/save", headers=seeker_headers)
    assert saved.status_code == 200
    assert client.get("/api/jobs/saved", headers=seeker_headers).json() == [{"job_id": job_id}]

    applied = client.post(
        "/api/applications",
        headers=seeker_headers,
        json={"job_id": job_id, "cover_letter": "I enjoy building software."},
    )
    assert applied.status_code == 200, applied.text
    application_id = applied.json()["application_id"]
    duplicate_application = client.post(
        "/api/applications",
        headers=seeker_headers,
        json={"job_id": job_id},
    )
    assert duplicate_application.status_code == 409

    recruiter_applications = client.get("/api/applications/recruiter", headers=recruiter_headers)
    assert recruiter_applications.status_code == 200
    assert recruiter_applications.json()[0]["id"] == application_id

    updated = client.patch(
        f"/api/applications/{application_id}/status",
        headers=recruiter_headers,
        json={"status": "Interview"},
    )
    assert updated.status_code == 200
    seeker_applications = client.get("/api/applications", headers=seeker_headers)
    assert seeker_applications.status_code == 200
    assert seeker_applications.json()[0]["status"] == "Interview"


def test_registration_and_protected_routes_enforce_roles(client: TestClient) -> None:
    admin_registration = client.post(
        "/api/auth/register",
        json={
            "full_name": "Attacker",
            "email": "attacker@example.com",
            "password": "password",
            "confirm_password": "password",
            "role": "admin",
        },
    )
    assert admin_registration.status_code == 400

    unauthenticated = client.get("/api/auth/me")
    assert unauthenticated.status_code == 403

    register_user(
        client,
        full_name="Sam Seeker",
        email="seeker@example.com",
        password="seeker-password",
        role="job_seeker",
    )
    seeker_headers = login(client, "seeker@example.com", "seeker-password")
    assert client.get("/api/admin/stats", headers=seeker_headers).status_code == 403
    assert client.get("/api/auth/me", headers=seeker_headers).json()["role"] == "job_seeker"


def test_resume_upload_download_is_owner_only(
    client: TestClient,
    test_directory: Path,
) -> None:
    register_user(
        client,
        full_name="Sam Seeker",
        email="seeker@example.com",
        password="seeker-password",
        role="job_seeker",
    )
    register_user(
        client,
        full_name="Taylor Seeker",
        email="other@example.com",
        password="other-password",
        role="job_seeker",
    )
    owner_headers = login(client, "seeker@example.com", "seeker-password")
    other_headers = login(client, "other@example.com", "other-password")

    from docx import Document
    from io import BytesIO

    document = Document()
    document.add_paragraph("Python, SQL, and data analysis experience.")
    content = BytesIO()
    document.save(content)
    content.seek(0)
    uploaded = client.post(
        "/api/resumes/upload",
        headers=owner_headers,
        files={
            "file": (
                "resume.docx",
                content.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert uploaded.status_code == 200, uploaded.text
    resume_id = uploaded.json()["resume_id"]
    assert "Python" in uploaded.json()["extracted_skills"]

    recommendations = client.get("/api/recommendations", headers=owner_headers)
    assert recommendations.status_code == 200, recommendations.text
    data_analyst = next(item for item in recommendations.json() if item["title"] == "Data Analyst")
    assert set(data_analyst["resume_matching_skills"]) == {"SQL", "Python"}
    assert set(data_analyst["missing_skills"]) == {"Excel", "Statistics", "Data Visualization", "Power BI"}
    assert data_analyst["score_breakdown"], "every recommendation explains its score"
    assert [step["title"] for step in data_analyst["career_roadmap"]] == [
        "Phase 1: Close your core gaps",
        "Phase 2: Strengthen what you partly know",
        "Phase 3: Build a proof-of-skill project",
        "Phase 4: Certify and get interview-ready",
    ]

    insights = client.get("/api/recommendations/insights", headers=owner_headers)
    assert insights.status_code == 200, insights.text
    assert insights.json()["top_skills_to_learn"]

    download = client.get(f"/api/resumes/{resume_id}/download", headers=owner_headers)
    assert download.status_code == 200
    assert download.content == content.getvalue()

    denied = client.get(f"/api/resumes/{resume_id}/download", headers=other_headers)
    assert denied.status_code == 404
    assert client.get(f"/api/resumes/{resume_id}/download").status_code == 403
    # Resumes live in the database now, never on the (ephemeral) serverless disk.
    assert not list((test_directory / "uploads").glob("resume_*"))
