"""Tests - Documents."""

from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.parcours import Parcours, ParcoursEtablissement
from app.models.user import UserRole
from tests.conftest import create_user, login_payload

def create_parcours(db) -> Parcours:
    parcours = Parcours(nom="Informatique", description="Parcours test", etablissement=ParcoursEtablissement.IIT)
    db.add(parcours)
    db.commit()
    db.refresh(parcours)
    return parcours


def create_candidate_token(client: TestClient, db, email: str = "cand-doc@test.com") -> tuple[dict, object]:
    user = create_user(db, "Candidat", email, role=UserRole.CANDIDAT)
    return login_payload(client, user.email), user


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_candidate_upload_and_download_document(client: TestClient, db_session, tmp_path: Path) -> None:
    from tests.conftest import create_user as _cu

    settings.DOCUMENT_STORAGE_PATH = str(tmp_path)
    parcours = create_parcours(db_session)
    token_response, candidate = create_candidate_token(client, db_session)
    candidature_response = client.post("/api/candidatures", json={"parcours_id": str(parcours.id)}, headers=auth(token_response["access_token"]))
    assert candidature_response.status_code == 201
    candidature_id = candidature_response.json()["id"]

    upload = client.post(
        f"/api/candidatures/{candidature_id}/documents",
        files={"file": ("cv.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        headers=auth(token_response["access_token"]),
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["id"]

    listing = client.get(f"/api/candidatures/{candidature_id}/documents", headers=auth(token_response["access_token"]))
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    download = client.get(f"/api/documents/{document_id}/download", headers=auth(token_response["access_token"]))
    assert download.status_code == 200
    assert b"%PDF-1.4" in download.content

    other_token, _ = create_candidate_token(client, db_session, "cand-doc-2@test.com")
    forbidden_download = client.get(f"/api/documents/{document_id}/download", headers=auth(other_token["access_token"]))
    assert forbidden_download.status_code in (403, 404)


def test_document_upload_invalid_extension(client: TestClient, db_session, tmp_path: Path) -> None:
    settings.DOCUMENT_STORAGE_PATH = str(tmp_path)
    parcours = create_parcours(db_session)
    token_response, _ = create_candidate_token(client, db_session)
    candidature_response = client.post("/api/candidatures", json={"parcours_id": str(parcours.id)}, headers=auth(token_response["access_token"]))
    candidature_id = candidature_response.json()["id"]

    upload = client.post(
        f"/api/candidatures/{candidature_id}/documents",
        files={"file": ("virus.exe", b"MZ fake exe content", "application/octet-stream")},
        headers=auth(token_response["access_token"]),
    )
    assert upload.status_code == 400
