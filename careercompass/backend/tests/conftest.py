from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

TEST_DIRECTORY = tempfile.TemporaryDirectory(prefix="careercompass-tests-")
TEST_ROOT = Path(TEST_DIRECTORY.name)
TEST_DATABASE_URL = str(URL.create("sqlite", database=str(TEST_ROOT / "test.db")))
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["UPLOAD_DIRECTORY"] = str(TEST_ROOT / "uploads")

from app.database import Base, get_db
from app.routers.auth import get_password_hash
from main import app

from app.database import engine

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        from app.models import User

        db.add(
            User(
                full_name="Test Admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin-password"),
                role="admin",
                is_active=True,
            )
        )
        db.commit()

    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


@pytest.fixture
def test_directory():
    return TEST_ROOT
