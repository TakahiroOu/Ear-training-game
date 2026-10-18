"""Shared test setup ("fixtures"). pytest finds this file automatically.

Database tests use the throwaway db-test container, never Supabase.
"""

import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


@pytest.fixture(scope="session")
def engine():
    """An empty test database with all migrations applied (this also tests the migrations)."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set: run tests with  docker compose exec backend pytest")
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        alembic_config = Config(str(ALEMBIC_INI))
        alembic_config.attributes["connection"] = connection
        command.upgrade(alembic_config, "head")
    return engine


@pytest.fixture
def db(engine):
    with Session(engine) as session:
        yield session
    with engine.begin() as connection:  # empty the tables after each test
        connection.execute(text("TRUNCATE profiles, game_sessions, answers RESTART IDENTITY CASCADE"))


@pytest.fixture
def user():
    return CurrentUser(id=uuid.uuid4(), email="student@example.com")


@pytest.fixture
def login_as():
    """Pretend a user is logged in (skips the Supabase token check, which test_auth.py tests)."""

    def login(user):
        app.dependency_overrides[get_current_user] = lambda: user

    return login


@pytest.fixture
def client(db, user, login_as):
    """API client logged in as `user`, using the test database."""
    app.dependency_overrides[get_db] = lambda: db
    login_as(user)
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def guest_client(db):
    """API client that is NOT logged in."""
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
