"""Routes - Entretiens et demandes de complement."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.session import Session, get_db
from app.models.user import User
from app.schemas.entretien import DemandeComplementRead, EntretienApproval, EntretienCreate, EntretienRead
from app.services.entretien_service import (
    approve_entretien,
    create_demande_complement,
    create_entretien,
    list_demandes_complement,
    list_entretiens,
)

router = APIRouter(prefix="", tags=["Entretiens"])


@router.get("/entretiens", response_model=list[EntretienRead], summary="Liste des entretiens accessibles")
def list_entretiens_endpoint(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[EntretienRead]:
    return list_entretiens(db, user)


@router.post("/candidatures/{candidature_id}/entretiens", response_model=EntretienRead, status_code=201, summary="Organisation d'un entretien")
def create_entretien_endpoint(
    candidature_id: UUID,
    entretien_create: EntretienCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EntretienRead:
    entretien = create_entretien(db, candidature_id, user, entretien_create)
    return EntretienRead.model_validate(entretien)


@router.patch("/entretiens/{entretien_id}/approval", response_model=EntretienRead, summary="Enregistrement de l'approbation d'entretien")
def approve_entretien_endpoint(
    entretien_id: UUID,
    entretien_approval: EntretienApproval,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EntretienRead:
    entretien = approve_entretien(db, entretien_id, user, entretien_approval)
    return EntretienRead.model_validate(entretien)
