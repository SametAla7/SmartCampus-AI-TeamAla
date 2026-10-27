"""Tests - Authentification."""

from fastapi.testclient import TestClient

from app.models.user import UserRole
from tests.conftest import create_user, login_payload


def test_login_success(client: TestClient, db_session) -> None:
    user = create_user(db_session, "Candidat Test", "candidat@test.com", role=UserRole.CANDIDAT)
    token_response = login_payload(client, user.email)
    assert "access_token" in token_response
    assert "refresh_token" in token_response
    assert token_response["user"]["email"] == user.email
    assert token_response["user"]["role"] == "CANDIDAT"
    assert "mot_de_passe" not in token_response["user"]


def test_login_wrong_password(client: TestClient, db_session) -> None:
    user = create_user(db_session, "Candidat Test", "candidat@test.com")
    response = client.post("/api/auth/login", json={"email": user.email, "mot_de_passe": "wrongpassword"})
    assert response.status_code == 401


def test_login_unknown_email(client: TestClient, db_session) -> None:
    response = client.post("/api/auth/login", json={"email": "unknown@test.com", "mot_de_passe": "password123"})
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient, db_session) -> None:
    user = create_user(db_session, "Candidat Test", "candidat@test.com")
    token_response = login_payload(client, user.email)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_response['access_token']}"})
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_refresh_returns_new_tokens(client: TestClient, db_session) -> None:
    user = create_user(db_session, "Candidat Test", "candidat@test.com")
    token_response = login_payload(client, user.email)
    response = client.post("/api/auth/refresh", json={"token": token_response["refresh_token"]})
    assert response.status_code == 200
    assert "access_token" in response.json()
