"""Tests - Parcours academiques."""

import uuid

from fastapi.testclient import TestClient

from app.models.parcours import Parcours, ParcoursEtablissement


def create_parcours(db, nom: str = "Informatique", etablissement: ParcoursEtablissement = ParcoursEtablissement.IIT) -> Parcours:
    parcours = Parcours(nom=nom, description="Parcours test", etablissement=etablissement)
    db.add(parcours)
    db.commit()
    db.refresh(parcours)
    return parcours


def test_list_parcours(client: TestClient, db_session) -> None:
    create_parcours(db_session, "Informatique", ParcoursEtablissement.IIT)
    create_parcours(db_session, "Business", ParcoursEtablissement.ISB)
    response = client.get("/api/parcours")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_get_parcours_by_id(client: TestClient, db_session) -> None:
    parcours = create_parcours(db_session)
    response = client.get(f"/api/parcours/{parcours.id}")
    assert response.status_code == 200
    assert response.json()["nom"] == "Informatique"


def test_get_parcours_not_found(client: TestClient, db_session) -> None:
    response = client.get(f"/api/parcours/{uuid.uuid4()}")
    assert response.status_code == 404


def test_list_parcours_filter_by_etablissement(client: TestClient, db_session) -> None:
    create_parcours(db_session, "Informatique", ParcoursEtablissement.IIT)
    create_parcours(db_session, "Business", ParcoursEtablissement.ISB)
    response = client.get("/api/parcours", params={"etablissement": "ISB"})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["etablissement"] == "ISB"
