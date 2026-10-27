"""Tests - Candidatures (depot, consultation, decisions academiques)."""

from uuid import UUID

from fastapi.testclient import TestClient

from app.models.candidature import Candidature as CandidatureModel, CandidatureStatut
from app.models.parcours import Parcours, ParcoursEtablissement
from app.models.user import UserRole
from tests.conftest import create_user, login_payload


def create_parcours(db) -> Parcours:
    parcours = Parcours(nom="Informatique", description="Parcours test", etablissement=ParcoursEtablissement.IIT)
    db.add(parcours)
    db.commit()
    db.refresh(parcours)
    return parcours


def create_candidate_token(client: TestClient, db, email: str = "cand@test.com") -> tuple[dict, object]:
    user = create_user(db, "Candidat", email, role=UserRole.CANDIDAT)
    return login_payload(client, user.email), user


def login_as_academic_manager(client: TestClient, db, email: str = "ra@test.com") -> str:
    from app.models.user import User

    existing = db.query(User).filter(User.email == email).first()
    if not existing:
        existing = create_user(db, "Responsable Academique", email, password="password123", role=UserRole.RESPONSABLE_ACADEMIQUE)
    return login_payload(client, existing.email)["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_candidature(client: TestClient, token: str, parcours_id: UUID) -> dict:
    response = client.post("/api/candidatures", json={"parcours_id": str(parcours_id)}, headers=auth(token))
    assert response.status_code == 201, response.text
    return response.json()


def assign_academic_manager(db, candidature_id, email: str = "ra@test.com") -> None:
    from uuid import UUID

    from app.models.user import User

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = create_user(db, "Responsable Academique", email, password="password123", role=UserRole.RESPONSABLE_ACADEMIQUE)
    if isinstance(candidature_id, str):
        candidature_id = UUID(candidature_id)
    candidature = db.query(CandidatureModel).filter(CandidatureModel.id == candidature_id).first()
    candidature.responsable_academique_id = user.id
    db.commit()


def test_candidate_creates_candidature(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    token_response, candidate = create_candidate_token(client, db_session)
    candidature = create_candidature(client, token_response["access_token"], parcours.id)
    assert candidature["statut"] == CandidatureStatut.EN_ATTENTE.value
    assert str(candidature["parcours"]["id"]) == str(parcours.id)
    assert str(candidature["candidat_id"]) == str(candidate.id)


def test_candidate_creates_candidature_unknown_parcours(client: TestClient, db_session) -> None:
    from uuid import uuid4

    token_response, _ = create_candidate_token(client, db_session)
    response = client.post("/api/candidatures", json={"parcours_id": str(uuid4())}, headers=auth(token_response["access_token"]))
    assert response.status_code == 404


def test_candidate_lists_only_own_candidatures(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    token_response_a, _ = create_candidate_token(client, db_session, "cand-a@test.com")
    token_response_b, _ = create_candidate_token(client, db_session, "cand-b@test.com")
    candidature_b = create_candidature(client, token_response_b["access_token"], parcours.id)

    response_a = client.get("/api/candidatures", headers=auth(token_response_a["access_token"]))
    response_b = client.get("/api/candidatures", headers=auth(token_response_b["access_token"]))

    assert response_a.status_code == 200
    assert response_a.json()["total"] == 0
    assert response_b.status_code == 200
    assert response_b.json()["total"] == 1
    assert response_b.json()["items"][0]["id"] == candidature_b["id"]


def test_candidate_cannot_access_others_candidature(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    token_response_a, _ = create_candidate_token(client, db_session, "cand-a@test.com")
    candidature = create_candidature(client, token_response_a["access_token"], parcours.id)
    token_response_b, _ = create_candidate_token(client, db_session, "cand-b@test.com")
    response = client.get(f"/api/candidatures/{candidature['id']}", headers=auth(token_response_b["access_token"]))
    assert response.status_code in (403, 404)


def test_academic_manager_accepts_candidature(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    token_response, _ = create_candidate_token(client, db_session)
    candidature = create_candidature(client, token_response["access_token"], parcours.id)
    assign_academic_manager(db_session, candidature["id"])

    ra_token = login_as_academic_manager(client, db_session)
    response = client.patch(
        f"/api/candidatures/{candidature['id']}/decision",
        json={"decision": "ACCEPTER", "commentaire": "Dossier complet"},
        headers=auth(ra_token),
    )
    assert response.status_code == 200
    assert response.json()["statut"] == CandidatureStatut.VALIDEE.value
    assert response.json()["decision"]["decision"] == "ACCEPTER"


def test_decision_rejet_then_conflict(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    token_response, _ = create_candidate_token(client, db_session)
    candidature = create_candidature(client, token_response["access_token"], parcours.id)
    assign_academic_manager(db_session, candidature["id"])

    ra_token = login_as_academic_manager(client, db_session)
    first = client.patch(f"/api/candidatures/{candidature['id']}/decision", json={"decision": "REJETER"}, headers=auth(ra_token))
    assert first.status_code == 200
    assert first.json()["statut"] == CandidatureStatut.REJETEE.value

    second = client.patch(f"/api/candidatures/{candidature['id']}/decision", json={"decision": "ACCEPTER"}, headers=auth(ra_token))
    assert second.status_code == 409
