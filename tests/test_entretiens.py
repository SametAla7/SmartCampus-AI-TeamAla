"""Tests - Entretiens et demandes de complement."""

from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.models.candidature import Candidature as CandidatureModel
from app.models.parcours import Parcours, ParcoursEtablissement
from app.models.user import UserRole
from tests.conftest import create_user, login_payload


def create_parcours(db) -> Parcours:
    parcours = Parcours(nom="Informatique", description="Parcours test", etablissement=ParcoursEtablissement.IIT)
    db.add(parcours)
    db.commit()
    db.refresh(parcours)
    return parcours


def create_candidate_token(client: TestClient, db, email: str = "cand-ent@test.com") -> tuple[dict, object]:
    user = create_user(db, "Candidat", email, role=UserRole.CANDIDAT)
    return login_payload(client, user.email), user


def create_interviewer_token(client: TestClient, db, email: str = "interviewer@test.com") -> str:
    user = create_user(db, "Responsable Entretien", email, password="password123", role=UserRole.RESPONSABLE_ENTRETIEN)
    return login_payload(client, user.email)["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_candidature(client: TestClient, token: str, parcours_id: UUID):
    response = client.post("/api/candidatures", json={"parcours_id": str(parcours_id)}, headers=auth(token))
    assert response.status_code == 201, response.text
    return response.json()


def test_interviewer_creates_entretien(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    candidature = create_candidature(client, create_candidate_token(client, db_session)[0]["access_token"], parcours.id)

    interviewer_token = create_interviewer_token(client, db_session)
    response = client.post(
        f"/api/candidatures/{candidature['id']}/entretiens",
        json={"date": "2030-06-15T10:00:00Z"},
        headers=auth(interviewer_token),
    )
    assert response.status_code == 201, response.text
    assert response.json()["approuve"] is False

    second = client.post(
        f"/api/candidatures/{candidature['id']}/entretiens",
        json={"date": "2030-06-16T10:00:00Z"},
        headers=auth(interviewer_token),
    )
    assert second.status_code == 409


def test_interviewer_sends_approval_then_cannot_revoke(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    candidature = create_candidature(client, create_candidate_token(client, db_session)[0]["access_token"], parcours.id)
    interviewer_token = create_interviewer_token(client, db_session)
    created = client.post(
        f"/api/candidatures/{candidature['id']}/entretiens",
        json={"date": "2030-06-15T10:00:00Z"},
        headers=auth(interviewer_token),
    )
    assert created.status_code == 201
    entretien_id = created.json()["id"]

    approved = client.patch(f"/api/entretiens/{entretien_id}/approval", json={"approuve": True}, headers=auth(interviewer_token))
    assert approved.status_code == 200
    assert approved.json()["approuve"] is True

    revoked = client.patch(f"/api/entretiens/{entretien_id}/approval", json={"approuve": False}, headers=auth(interviewer_token))
    assert revoked.status_code == 409


def test_interviewer_creates_demande_complement(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    candidature = create_candidature(client, create_candidate_token(client, db_session)[0]["access_token"], parcours.id)
    interviewer_token = create_interviewer_token(client, db_session)
    response = client.post(
        f"/api/candidatures/{candidature['id']}/demandes-complement",
        json={"contenu": "Merci de preciser votre experience professionnelle.", "informations_attendues": "Experience en entreprise"},
        headers=auth(interviewer_token),
    )
    assert response.status_code == 201, response.text
    assert response.json()["statut"] == "EN_ATTENTE"
