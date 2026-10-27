"""Tests - Utilisateurs (gestion par un administrateur)."""

from fastapi.testclient import TestClient

from app.models.user import UserRole


def get_admin_token(client: TestClient, db_session) -> str:
    from tests.conftest import create_user, login_payload

    admin = create_user(db_session, "Admin", "admin@test.com", password="password123", role=UserRole.ADMINISTRATEUR)
    return login_payload(client, admin.email)["access_token"]


def test_candidate_cannot_list_users(client: TestClient, db_session) -> None:
    from tests.conftest import create_user, login_payload

    candidate = create_user(db_session, "Candidat", "candidat2@test.com", role=UserRole.CANDIDAT)
    token_response = login_payload(client, candidate.email)
    response = client.get("/api/users", headers={"Authorization": f"Bearer {token_response['access_token']}"})
    assert response.status_code == 403


def test_admin_creates_user(client: TestClient, db_session) -> None:
    headers = {"Authorization": f"Bearer {get_admin_token(client, db_session)}"}
    response = client.post(
        "/api/users",
        json={"nom": "Nouvel Admin", "email": "nouvel@test.com", "mot_de_passe": "password123", "role": "ADMINISTRATEUR"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["email"] == "nouvel@test.com"


def test_admin_lists_users(client: TestClient, db_session) -> None:
    headers = {"Authorization": f"Bearer {get_admin_token(client, db_session)}"}
    response = client.get("/api/users", params={"page": 1, "limit": 10}, headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_admin_deactivates_user(client: TestClient, db_session) -> None:
    headers = {"Authorization": f"Bearer {get_admin_token(client, db_session)}"}
    response = client.post(
        "/api/users",
        json={"nom": "User Test", "email": "user-test@test.com", "mot_de_passe": "password123", "role": "CANDIDAT"},
        headers=headers,
    )
    assert response.status_code == 201
    user_id = response.json()["id"]
    response = client.patch(f"/api/users/{user_id}/status", json={"est_actif": False}, headers=headers)
    assert response.status_code == 200
    assert response.json()["est_actif"] is False
