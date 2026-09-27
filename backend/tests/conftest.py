"""
Test configuration.

Uses an in-memory SQLite database instead of Postgres for speed and zero
external dependency in CI. This is safe for our purposes because we
avoid Postgres-only SQL in application code paths under test — the one
exception (JSONB in AuditLog) still works fine under SQLite for these
tests since we never query its internal structure here.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite ignores ON DELETE CASCADE unless foreign key enforcement is
    # explicitly turned on per connection. Enabling it here means the
    # test suite exercises the same cascade behavior Postgres applies
    # natively in production, instead of silently skipping it.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def isolated_evidence_storage(tmp_path, monkeypatch):
    """
    Evidence uploads write real files to disk. Point that at a pytest
    tmp_path for the duration of each test instead of the container
    path (/app/storage/evidence), which won't exist — or be writable —
    outside Docker.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "evidence_storage_path", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
