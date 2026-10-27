# CareerCompass AI

Full-stack career recommendation and job portal for students and recruiters.

- **Frontend:** React + Vite + TypeScript
- **Backend:** Python + FastAPI + SQLAlchemy
- **Database:** SQLite locally, Postgres in production (Vercel)

## The recommendation engine (v2)

Scores are a transparent weighted average of independent components, and the UI shows the breakdown for every career and job ("How this score is calculated").

| Component | Careers | Jobs | What it measures |
|---|---|---|---|
| Skills | 70% | 60% | IDF-weighted coverage of required (75%) + recommended (25%) skills |
| Nice-to-have skills | – | 8% | Skills mentioned in the job's preferred qualifications |
| Goal / role fit | 15% | 15% | Career goal text vs. the role (handles "engineer" ≈ "developer", etc.) |
| Experience | 9% | 12% | Years of experience (parsed from dates) vs. seniority expected |
| Education | 6% | – | Education level and field vs. what the career asks for |
| Work mode / location | – | 5% | Matches your saved preferences |

What makes it smarter than keyword matching:

- **Partial credit.** A knowledge graph knows React implies JavaScript, PostgreSQL implies SQL, PyTorch ≈ TensorFlow, Power BI ≈ Tableau, etc. These show up as "≈ 72%" chips with the skill they came from.
- **Rarity weighting (IDF).** Distinctive skills (Kubernetes, Figma) count for more than skills almost every career lists (Git).
- **Proficiency and proof.** Skill proficiency (1-5) scales credit. Skills backed by a resume, project or certification are rated higher than skills that are only claimed.
- **No silent defaults.** If a component can't be judged (e.g. no career goal entered) it is left out and the rest is re-normalised instead of being scored as "50%".
- **Personalised output.** Readiness label, estimated weeks to job-ready, ordered skill gaps, a roadmap built from *your* gaps, and a "learn these next" panel showing which single skills unlock the most of your top matches.

API: `GET /api/recommendations`, `GET /api/recommendations/insights`, `GET /api/recommendations/jobs`, `POST /api/recommendations/roadmap`.

## Deploy to Vercel

The repo deploys as **one Vercel project**: the Vite build is served statically and the FastAPI app runs as a serverless function (`api/index.py`) behind `/api/*`. `vercel.json` already wires this up.

1. **Push to GitHub** (`.gitignore` already excludes `.venv`, `node_modules`, `*.db`, `uploads/`).
2. **Create a Postgres database.** Vercel serverless storage is ephemeral, so real data needs Postgres. In Vercel: *Storage → Create → Neon (Postgres)* and connect it to the project. It injects `POSTGRES_URL` automatically (or set `DATABASE_URL` yourself).
3. **Import the repo** at vercel.com/new. Leave the framework preset as **Other**; build settings come from `vercel.json`.
4. **Set environment variables** (Project → Settings → Environment Variables):

   | Variable | Value |
   |---|---|
   | `SECRET_KEY` | **Required.** Long random string: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. The API refuses to start on Vercel without it. |
   | `DATABASE_URL` | Postgres URL, unless the Neon integration already set `POSTGRES_URL`. |
   | `AUTO_SEED` | `true` once, to load demo jobs/accounts into the empty database (then remove it). |

5. **Deploy.** Check `https://<your-app>.vercel.app/api/health`; it should report `"database": "postgres"`.

Seeding alternatives: run `DATABASE_URL=<your postgres url> python backend/seed.py` from your machine.

> **Security:** the demo accounts (`*@careercompass.ai` / `career123`) have a public password. Seed them for a demo, then delete or change them before sharing the site widely.

### Things that behave differently on Vercel

- **No Postgres configured?** The API falls back to a throw-away SQLite file in `/tmp` and auto-seeds it, so the site still works as a demo, but data resets on cold starts and differs between instances. `/api/health` shows `"database": "sqlite-demo"`.
- **Resumes are stored in the database**, not on disk. Upload limit is 4 MB (Vercel rejects request bodies above ~4.5 MB).
- Old databases get the new `resumes.file_data` column added automatically on startup.

## Local setup

1. Create a virtual environment and install dependencies:

       python -m venv .venv
       .\.venv\Scripts\activate
       pip install -r backend\requirements.txt

2. Copy environment variables: `copy .env.example .env`
3. Seed the database: `python backend\seed.py`
4. Start the API from the project root:

       .\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000

5. In a second terminal:

       cd frontend
       npm install
       npm run dev -- --host 127.0.0.1

6. Open http://127.0.0.1:5173 (Vite proxies `/api` to port 8000).

## Tests

    pip install -r backend\requirements-dev.txt
    .\.venv\Scripts\python.exe -m pytest backend\tests

`test_recommendation_engine.py` is pure Python; `test_workflows.py` exercises the API against an isolated temporary SQLite database.

## Demo accounts

- Job seeker: seeker@careercompass.ai / career123
- Recruiter: recruiter@careercompass.ai / career123
- Admin: admin@careercompass.ai / career123

## Notes

- Seeded recruiter can post jobs for its verified company; new recruiter companies need admin verification.
- PDF/DOCX resumes are parsed for selectable text and known skills (including aliases such as "ReactJS", "Postgres", "k8s"). Scanned-image OCR is not included.
