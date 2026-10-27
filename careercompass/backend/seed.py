from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy import select

from app.database import SessionLocal, Base, engine
from app.models import User, JobSeekerProfile, RecruiterProfile, Company, Skill, Job, Career, CommunityPost, Notification
from app.recommendation import CAREER_CATALOG

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


EXPANDED_JOBS = [
    {
        "title": "Data Analyst",
        "description": "Analyze product and customer data to support feature decisions, identify growth levers, and present insights to leaders.",
        "responsibilities": "Build dashboards, validate metrics, present insights, clean datasets.",
        "required_skills": "SQL, Excel, Data Analysis, Python",
        "preferred_qualifications": "Power BI experience, data storytelling, and Tableau experience.",
        "education": "Bachelor's degree in Analytics, Statistics, or CS",
        "experience": "0-2 years",
        "employment_type": "Full-time",
        "salary_range": "₹12-18 LPA",
        "location": "Bengaluru",
        "work_mode": "Hybrid",
        "deadline": "2026-12-31",
        "openings": 3,
    },
    {
        "title": "Frontend Developer",
        "description": "Build clean, responsive, and accessible user interfaces for enterprise cloud software products.",
        "responsibilities": "Implement UI components in React, optimize Core Web Vitals, collaborate with designers.",
        "required_skills": "React, JavaScript, CSS, HTML",
        "preferred_qualifications": "TypeScript, Tailwind CSS, accessibility standards.",
        "education": "Bachelor's degree in CS or related field",
        "experience": "1-3 years",
        "employment_type": "Full-time",
        "salary_range": "₹15-22 LPA",
        "location": "Remote",
        "work_mode": "Remote",
        "deadline": "2026-11-20",
        "openings": 2,
    },
    {
        "title": "Backend Developer",
        "description": "Architect high-performance REST APIs, database schemas, and background worker queues for scalable cloud microservices.",
        "responsibilities": "Design and maintain REST APIs, optimize SQL database queries, configure Redis caching.",
        "required_skills": "Python, SQL, APIs, Databases",
        "preferred_qualifications": "Docker, Redis, FastAPI, PostgreSQL, System Design.",
        "education": "Bachelor's or Master's in Computer Science",
        "experience": "1-4 years",
        "employment_type": "Full-time",
        "salary_range": "₹16-25 LPA",
        "location": "Hyderabad",
        "work_mode": "Hybrid",
        "deadline": "2026-12-15",
        "openings": 4,
    },
    {
        "title": "Full-Stack Developer",
        "description": "Deliver end-to-end features spanning React frontend interfaces and Python/Node backend services.",
        "responsibilities": "Develop complete product workflows, integrate payment APIs, manage database models.",
        "required_skills": "JavaScript, React, Python, SQL",
        "preferred_qualifications": "Docker, AWS, REST APIs, Git, Next.js.",
        "education": "Bachelor's in Computer Science or IT",
        "experience": "1-3 years",
        "employment_type": "Full-time",
        "salary_range": "₹18-28 LPA",
        "location": "Pune",
        "work_mode": "Remote",
        "deadline": "2026-12-25",
        "openings": 3,
    },
    {
        "title": "Machine Learning Engineer",
        "description": "Build, evaluate, and deploy scalable machine learning models and inference services for intelligent platform capabilities.",
        "responsibilities": "Train predictive models, build automated feature pipelines, deploy ML services with Docker.",
        "required_skills": "Python, Machine Learning, Statistics, Data Modeling",
        "preferred_qualifications": "PyTorch, TensorFlow, MLOps, Scikit-learn, SQL.",
        "education": "Master's or Bachelor's in CS, AI, or Data Science",
        "experience": "1-3 years",
        "employment_type": "Full-time",
        "salary_range": "₹20-32 LPA",
        "location": "Bengaluru",
        "work_mode": "Hybrid",
        "deadline": "2026-11-30",
        "openings": 2,
    },
    {
        "title": "Data Scientist",
        "description": "Extract actionable patterns from multi-terabyte data to solve complex algorithmic and business problems.",
        "required_skills": "Python, Statistics, Machine Learning, SQL",
        "responsibilities": "Hypothesis testing, exploratory data analysis, predictive statistical modeling.",
        "preferred_qualifications": "Pandas, Scikit-learn, Data Visualization, experimentation.",
        "education": "Master's or Bachelor's in Statistics, CS, or Mathematics",
        "experience": "0-3 years",
        "employment_type": "Full-time",
        "salary_range": "₹16-26 LPA",
        "location": "Gurugram",
        "work_mode": "Hybrid",
        "deadline": "2026-12-10",
        "openings": 3,
    },
    {
        "title": "Cloud / DevOps Engineer",
        "description": "Build reliable continuous integration and delivery pipelines, automate cloud infrastructure, and maintain 99.9% uptime.",
        "responsibilities": "Automate CI/CD pipelines, manage Kubernetes clusters, configure Terraform infrastructure.",
        "required_skills": "Linux, Docker, CI/CD, Cloud",
        "preferred_qualifications": "Kubernetes, AWS, Terraform, Prometheus, Python.",
        "education": "Bachelor's degree in Computer Science or Engineering",
        "experience": "1-3 years",
        "employment_type": "Full-time",
        "salary_range": "₹18-27 LPA",
        "location": "Remote",
        "work_mode": "Remote",
        "deadline": "2026-12-20",
        "openings": 2,
    },
    {
        "title": "Cybersecurity Analyst",
        "description": "Protect critical infrastructure and company assets by analyzing vulnerability logs and monitoring telemetry for intrusions.",
        "responsibilities": "Monitor SIEM alerts, perform vulnerability assessments, assist with compliance audits.",
        "required_skills": "Networking, Security, Linux, Risk Analysis",
        "preferred_qualifications": "CompTIA Security+, ethical hacking, Wireshark, Splunk.",
        "education": "Bachelor's in Cybersecurity, IT, or Computer Science",
        "experience": "0-2 years",
        "employment_type": "Full-time",
        "salary_range": "₹14-20 LPA",
        "location": "Mumbai",
        "work_mode": "Onsite",
        "deadline": "2026-12-15",
        "openings": 2,
    },
    {
        "title": "UI/UX Designer",
        "description": "Design intuitive, delightful user flows, wireframes, and design systems for web and mobile products.",
        "responsibilities": "Conduct user interviews, design high-fidelity Figma components, prototype interactions.",
        "required_skills": "Figma, UI/UX, User Research, Wireframing",
        "preferred_qualifications": "Design systems, usability testing, basic HTML/CSS knowledge.",
        "education": "Degree in Interaction Design, Human-Computer Interaction, or Portfolio equivalent",
        "experience": "0-3 years",
        "employment_type": "Full-time",
        "salary_range": "₹12-20 LPA",
        "location": "Bengaluru",
        "work_mode": "Hybrid",
        "deadline": "2026-11-28",
        "openings": 2,
    },
    {
        "title": "Product Manager",
        "description": "Lead product roadmap planning, define customer requirements, and coordinate cross-functional teams from concept to launch.",
        "responsibilities": "Author PRDs, manage sprint backlogs, analyze user funnel analytics, communicate with stakeholders.",
        "required_skills": "Product Management, Agile, User Research, Data Analysis",
        "preferred_qualifications": "SQL, Scrum certification, roadmapping tools, technical communication.",
        "education": "Bachelor's or Master's in Business, Engineering, or CS",
        "experience": "1-4 years",
        "employment_type": "Full-time",
        "salary_range": "₹22-35 LPA",
        "location": "Bengaluru",
        "work_mode": "Hybrid",
        "deadline": "2026-12-31",
        "openings": 2,
    },
    {
        "title": "Mobile App Developer (Flutter / React Native)",
        "description": "Develop high-performance, cross-platform mobile apps for iOS and Android with sleek native animations.",
        "responsibilities": "Build mobile user interfaces, integrate RESTful APIs, maintain local SQLite/Hive caching.",
        "required_skills": "Flutter, React Native, JavaScript, Mobile Development",
        "preferred_qualifications": "Dart, Swift, Kotlin, state management (Bloc/Redux), App Store publishing.",
        "education": "Bachelor's in CS, IT, or self-taught app portfolio",
        "experience": "0-2 years",
        "employment_type": "Full-time",
        "salary_range": "₹14-22 LPA",
        "location": "Remote",
        "work_mode": "Remote",
        "deadline": "2026-12-18",
        "openings": 3,
    },
    {
        "title": "QA Automation Engineer",
        "description": "Ensure the highest product quality by developing automated integration, regression, and end-to-end test suites.",
        "responsibilities": "Build automated browser test suites with Playwright/Selenium, run automated API tests, report defects.",
        "required_skills": "Testing, Selenium, Python, Automation",
        "preferred_qualifications": "Playwright, Cypress, Postman, CI/CD integration, SQL.",
        "education": "Bachelor's degree in CS, Software Engineering, or IT",
        "experience": "0-2 years",
        "employment_type": "Full-time",
        "salary_range": "₹10-16 LPA",
        "location": "Noida",
        "work_mode": "Hybrid",
        "deadline": "2026-12-05",
        "openings": 3,
    },
]


def seed_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create demo admin if not present
    demo_admin = db.query(User).filter(User.email == "admin@careercompass.ai").first()
    if not demo_admin:
        demo_admin = User(
            full_name="Platform Admin",
            email="admin@careercompass.ai",
            password_hash=hash_password("career123"),
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db.add(demo_admin)
        db.flush()

    # Create demo job seeker if not present
    demo_job_seeker = db.query(User).filter(User.email == "seeker@careercompass.ai").first()
    if not demo_job_seeker:
        demo_job_seeker = User(
            full_name="Aisha Sharma",
            email="seeker@careercompass.ai",
            password_hash=hash_password("career123"),
            role="job_seeker",
            is_active=True,
            is_verified=True,
        )
        db.add(demo_job_seeker)
        db.flush()
        db.add(JobSeekerProfile(
            user_id=demo_job_seeker.id,
            education_level="Bachelor's degree in Computer Science",
            phone_number="+91 9876543210",
            preferred_location="Bengaluru",
            work_mode="Hybrid",
            salary_expectation="₹14-20 LPA",
            career_goals="Become a top Data Analyst or Software Engineer with strong analytical & coding skills.",
            skills_summary="Python, SQL, Excel, Data Analysis, JavaScript, React, Communication",
            profile_completion=85,
        ))

    # Create demo recruiter and company
    demo_recruiter = db.query(User).filter(User.email == "recruiter@careercompass.ai").first()
    if not demo_recruiter:
        demo_recruiter = User(
            full_name="Rohan Mehta",
            email="recruiter@careercompass.ai",
            password_hash=hash_password("career123"),
            role="recruiter",
            is_active=True,
            is_verified=True,
        )
        db.add(demo_recruiter)
        db.flush()
        db.add(RecruiterProfile(
            user_id=demo_recruiter.id,
            recruiter_name="Rohan Mehta",
            company_name="NovaStack Labs",
            company_website="https://novastack.example",
            company_description="Builds AI-assisted productivity products and high-performance cloud tools.",
            industry="Software & AI",
            company_size="201-500 employees",
            verification_status="verified",
        ))

    company = db.query(Company).filter(Company.name == "NovaStack Labs").first()
    if not company:
        company = Company(
            name="NovaStack Labs",
            website="https://novastack.example",
            description="Building AI-powered software products and analytics infrastructure for enterprise teams.",
            industry="Software & AI",
            location="Bengaluru",
            is_verified=True,
        )
        db.add(company)
        db.flush()

    # Populate skills
    all_skills_list = [
        "Python", "SQL", "Excel", "Tableau", "Power BI", "JavaScript", "React",
        "Machine Learning", "Data Analysis", "Communication", "Docker", "Kubernetes",
        "Linux", "AWS", "Azure", "CI/CD", "Git", "Figma", "UI/UX", "User Research",
        "Wireframing", "Product Management", "Agile", "Scrum", "Flutter", "React Native",
        "Testing", "Selenium", "Playwright", "Cypress", "Postman", "PostgreSQL",
    ]
    for name in all_skills_list:
        existing_skill = db.query(Skill).filter(Skill.name == name).first()
        if not existing_skill:
            db.add(Skill(name=name, category="general"))
    db.flush()

    # Populate careers
    for career in CAREER_CATALOG:
        existing_career = db.query(Career).filter(Career.title == career["title"]).first()
        if not existing_career:
            db.add(Career(
                title=career["title"],
                description=career["description"],
                required_skills=", ".join(career["required_skills"]),
                recommended_skills=", ".join(career["recommended_skills"]),
                education=career["education"],
                responsibilities=", ".join(career["responsibilities"]),
                learning_roadmap="; ".join(p["phase"] + ": " + ", ".join(p["topics"]) for p in career.get("roadmap_phases", [])),
                suggested_projects=", ".join(career["projects"]),
                certifications=", ".join(career["certifications"]),
                related_jobs=", ".join(career["related_jobs"]),
            ))
    db.flush()

    # Populate expanded jobs
    for job_info in EXPANDED_JOBS:
        existing_job = db.query(Job).filter(Job.title == job_info["title"]).first()
        if not existing_job:
            db.add(Job(
                company_id=company.id,
                title=job_info["title"],
                description=job_info["description"],
                responsibilities=job_info["responsibilities"],
                required_skills=job_info["required_skills"],
                preferred_qualifications=job_info["preferred_qualifications"],
                education=job_info["education"],
                experience=job_info["experience"],
                employment_type=job_info["employment_type"],
                salary_range=job_info["salary_range"],
                location=job_info["location"],
                work_mode=job_info["work_mode"],
                deadline=job_info["deadline"],
                openings=job_info["openings"],
                is_active=True,
            ))
    db.flush()

    if db.query(CommunityPost).count() == 0:
        db.add(CommunityPost(
            user_id=demo_job_seeker.id,
            title="How do I build a strong data analytics portfolio?",
            content="I am preparing for data analyst and software engineering roles. What projects stand out most to hiring managers?",
            category="Career Guidance",
            tags="analytics, portfolio, data, career",
        ))

    db.commit()
    db.close()


if __name__ == "__main__":
    seed_database()
    print("Database seeded with expanded jobs, catalog, and career roadmaps successfully.")
