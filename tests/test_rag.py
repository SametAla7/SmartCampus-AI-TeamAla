"""Tests - Administration RAG (non operationnelle tant que non configuree)."""

from fastapi.testclient import TestClient

from app.models.user import UserRole
from tests.conftest import create_user, login_payload


def test_admin_rag_reindex_not_configured(client: TestClient, db_session) -> None:
    admin = create_user(db_session, "Admin RAG", "admin-rag@test.com", password="password123", role=UserRole.ADMINISTRATEUR)
    token_response = login_payload(client, admin.email)
    response = client.post("/api/admin/rag/reindex", headers={"Authorization": f"Bearer {token_response['access_token']}"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "RAG_NOT_CONFIGURED"


def test_candidate_cannot_access_admin_rag(client: TestClient, db_session) -> None:
    candidate = create_user(db_session, "Candidat RAG", "cand-rag@test.com", role=UserRole.CANDIDAT)
    token_response = login_payload(client, candidate.email)
    response = client.get("/api/admin/rag/status", headers={"Authorization": f"Bearer {token_response['access_token']}"})
    assert response.status_code == 403
