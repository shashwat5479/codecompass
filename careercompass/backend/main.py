from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = str(Path(__file__).resolve().parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import DATABASE_MODE, SessionLocal, ensure_schema
from app.models import User
from app.routers import admin, applications, auth, community, jobs, profiles, recommendations, resumes

ensure_schema()


def _seed_if_empty() -> None:
    """Seed demo data into an empty database.

    Automatic only for the throw-away SQLite demo DB; for Postgres set AUTO_SEED=true
    (or run `python backend/seed.py` once) because the demo accounts use a public password.
    """
    enabled = settings.auto_seed if settings.auto_seed is not None else DATABASE_MODE == "sqlite-demo"
    if not enabled:
        return
    with SessionLocal() as db:
        if db.query(User).count() > 0:
            return
    from seed import seed_database

    seed_database()


_seed_if_empty()

app = FastAPI(title="CareerCompass AI", version="1.1.0")

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    # Credentials can't be combined with the "*" wildcard; auth uses a bearer header anyway.
    allow_credentials=_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (auth, profiles, jobs, applications, community, admin, resumes, recommendations):
    app.include_router(module.router)


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "CareerCompass AI", "database": DATABASE_MODE}
