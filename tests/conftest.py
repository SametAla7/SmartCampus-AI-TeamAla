"""Fixtures de tests - base SQLite en memoire et client FastAPI."""

import os

# Allow isolated SQLite test DB even when app enforces hosted Postgres in normal mode.
os.environ.setdefault("SMARTCAMPUS_ALLOW_NON_REMOTE_DB", "1")

import uuid
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.core import security
import app.models  # ensure all models are imported so metadata is populated
from app.models.user import User, UserRole
from app.main import app
from app.db.session import get_db

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _isolate_external_services(monkeypatch):
    """Les tests ne doivent jamais envoyer de vrais emails ni appeler Google,
    meme si le .env du developpeur contient de vrais identifiants."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:4200")


@pytest.fixture()
def db_session() -> Iterator:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture()
def client(db_session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def create_user(db, nom: str, email: str, password: str = "password123", role: UserRole = UserRole.CANDIDAT, est_actif: bool = True) -> User:
    user = User(
        nom=nom,
        email=email,
        mot_de_passe=security.hash_password(password),
        role=role,
        est_actif=est_actif,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_payload(client: TestClient, email: str, mot_de_passe: str = "password123") -> dict:
    response = client.post("/api/auth/login", json={"email": email, "mot_de_passe": mot_de_passe})
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
