from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import DEFAULT_SQLITE_URL, ON_VERCEL, settings

# Query parameters some hosted-Postgres integrations add that psycopg2 rejects.
_UNSUPPORTED_QUERY_PARAMS = {"supa", "pgbouncer"}


def _normalise_postgres_url(url: str) -> str:
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg2://" + url[len(prefix):]
            break
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in _UNSUPPORTED_QUERY_PARAMS]
    return urlunsplit(parts._replace(query=urlencode(query)))


def resolve_database_url() -> tuple[str | URL, str]:
    """Pick the database and say which mode we're in: 'postgres', 'sqlite-demo' or 'sqlite'."""
    explicit = settings.database_url
    if explicit and explicit != DEFAULT_SQLITE_URL:
        if explicit.startswith(("postgres://", "postgresql")):
            return _normalise_postgres_url(explicit), "postgres"
        return explicit, "sqlite"

    # Vercel Postgres / Neon / Supabase integrations inject these names.
    for name in ("POSTGRES_URL", "POSTGRES_URL_NON_POOLING", "POSTGRES_PRISMA_URL"):
        value = os.getenv(name)
        if value:
            return _normalise_postgres_url(value), "postgres"

    if ON_VERCEL:
        # The deployment filesystem is read-only except /tmp, which is wiped between
        # cold starts. Fine for a demo, NOT for real data -> connect Postgres for that.
        return URL.create("sqlite", database="/tmp/careercompass.db"), "sqlite-demo"

    return URL.create("sqlite", database=str(Path(__file__).resolve().parents[2] / "careercompass.db")), "sqlite"


database_url, DATABASE_MODE = resolve_database_url()

_engine_kwargs: dict = {}
if DATABASE_MODE.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
elif ON_VERCEL:
    # Each invocation may land on a fresh container; let the DB's pooler do the pooling.
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_pre_ping"] = True

engine = create_engine(database_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """Create missing tables and add columns introduced after a database was first created."""
    from app import models  # noqa: F401  (registers tables on Base.metadata)

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if inspector.has_table("resumes"):
        columns = {column["name"] for column in inspector.get_columns("resumes")}
        if "file_data" not in columns:
            column_type = "BYTEA" if engine.dialect.name == "postgresql" else "BLOB"
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE resumes ADD COLUMN file_data {column_type}"))
