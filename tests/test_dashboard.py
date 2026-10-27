"""Tests - Tableau de bord (statistiques + export)."""

from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.models.candidature import Candidature as CandidatureModel, CandidatureStatut
from app.models.parcours import Parcours, ParcoursEtablissement
from app.models.user import UserRole
from tests.conftest import create_user, login_payload


def create_direction_token(client: TestClient, db) -> str:
    user = create_user(db, "Direction", "direction@test.com", password="password123", role=UserRole.DIRECTION)
    return login_payload(client, user.email)["access_token"]


def create_parcours(db) -> Parcours:
    parcours = Parcours(nom="Informatique", description="Parcours test", etablissement=ParcoursEtablissement.IIT)
    db.add(parcours)
    db.commit()
    db.refresh(parcours)
    return parcours


def test_direction_dashboard_stats(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    c1 = CandidatureModel(candidat_id=UUID("11111111-1111-1111-1111-111111111111"), parcours_id=parcours.id, statut=CandidatureStatut.EN_ATTENTE)
    c2 = CandidatureModel(candidat_id=UUID("22222222-2222-2222-2222-222222222222"), parcours_id=parcours.id, statut=CandidatureStatut.VALIDEE)
    db_session.add_all([c1, c2])
    db_session.commit()

    token = create_direction_token(client, db_session)
    response = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["total_candidatures"] == 2
    assert response.json()["candidatures_par_statut"]["EN_ATTENTE"] == 1
    assert response.json()["candidatures_par_statut"]["VALIDEE"] == 1


def test_direction_dashboard_export_pdf(client: TestClient, db_session) -> None:
    token = create_direction_token(client, db_session)
    response = client.get("/api/dashboard/export", params={"format": "pdf"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")


def test_direction_dashboard_export_xlsx(client: TestClient, db_session) -> None:
    token = create_direction_token(client, db_session)
    response = client.get("/api/dashboard/export", params={"format": "xlsx"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]


def test_direction_dashboard_export_invalid_format(client: TestClient, db_session) -> None:
    token = create_direction_token(client, db_session)
    response = client.get("/api/dashboard/export", params={"format": "csv"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_candidate_cannot_access_dashboard(client: TestClient, db_session) -> None:
    candidate = create_user(db_session, "Candidat Direction", "cand-dir@test.com", role=UserRole.CANDIDAT)
    token_response = login_payload(client, candidate.email)
    response = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token_response['access_token']}"})
    assert response.status_code == 403
