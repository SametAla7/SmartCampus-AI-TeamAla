"""Routes - Parcours academiques."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db.session import Session, get_db
from app.schemas.parcours import ParcoursEtablissementEnum, ParcoursListResponse, ParcoursRead
from app.services.parcours_service import get_parcours, list_parcours

router = APIRouter(prefix="/parcours", tags=["Parcours"])


@router.get("", response_model=ParcoursListResponse, summary="Liste des parcours (filtrable par etablissement)")
def list_parcours_endpoint(
    etablissement: str | None = Query(default=None, description="IIT | ISB"),
    db: Session = Depends(get_db),
) -> ParcoursListResponse:
    return list_parcours(db, etablissement=etablissement)


@router.get("/{parcours_id}", response_model=ParcoursRead, summary="Detail d'un parcours")
def get_parcours_endpoint(parcours_id: UUID, db: Session = Depends(get_db)) -> ParcoursRead:
    return ParcoursRead.model_validate(get_parcours(db, parcours_id))
