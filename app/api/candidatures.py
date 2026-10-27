"""Routes - Candidatures."""

from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Query, status, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import forbidden
from app.db.session import Session as DBSession, get_db
from app.models.user import User, UserRole
from app.schemas.candidature import CandidatureCreate, CandidatureDecision, CandidatureListResponse, CandidatureRead, DecisionCandidatureEnum
from app.schemas.document import DocumentRead
from app.schemas.entretien import DemandeComplementCreate, DemandeComplementRead
from app.schemas.qcm import QCMRead, QCMResultRead, QCMSubmit
from app.services.candidature_service import (
    create_candidature,
    decide_candidature,
    get_candidature_for_user,
    get_qcm_for_user,
    get_qcm_result_for_user,
    list_candidatures,
    submit_qcm_for_user,
    to_candidature_read,
)
from app.services.document_service import add_document, list_documents
from app.services.entretien_service import create_demande_complement, list_demandes_complement

router = APIRouter(prefix="/candidatures", tags=["Candidatures"])


@router.post("", response_model=CandidatureRead, status_code=status.HTTP_201_CREATED, summary="Depot d'une candidature")
def create_candidature_endpoint(user: User = Depends(get_current_user), data: CandidatureCreate = Body(...), db: Session = Depends(get_db)) -> CandidatureRead:
    if user.role != UserRole.CANDIDAT:
        raise forbidden("FORBIDDEN_ROLE", "Seuls les candidats peuvent deposer une candidature.")
    candidature = create_candidature(db, user, data)
    return to_candidature_read(db, candidature)


@router.get("", response_model=CandidatureListResponse, summary="Liste des candidatures (selon le role)")
def list_candidatures_endpoint(
    statut: str | None = None,
    parcours_id: UUID | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidatureListResponse:
    return list_candidatures(db, user, statut=statut, parcours_id=parcours_id, page=page, limit=limit)


@router.get("/{candidature_id}", response_model=CandidatureRead, summary="Consultation d'une candidature")
def get_candidature_endpoint(candidature_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CandidatureRead:
    candidature = get_candidature_for_user(db, candidature_id, user)
    return to_candidature_read(db, candidature)


@router.patch("/{candidature_id}/decision", response_model=CandidatureRead, summary="Decision academique (accepter / rejeter / reorienter)")
def decide_candidature_endpoint(
    candidature_id: UUID,
    decision_data: CandidatureDecision,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidatureRead:
    return decide_candidature(db, candidature_id, user, decision_data.decision, decision_data.commentaire, decision_data.parcours_destination_id)


@router.get("/{candidature_id}/qcm", response_model=QCMRead, summary="Consultation du QCM autorise pour la candidature")
def get_qcm_endpoint(candidature_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> QCMRead:
    return get_qcm_for_user(db, candidature_id, user)


@router.post("/{candidature_id}/qcm/submit", response_model=QCMRead, status_code=status.HTTP_201_CREATED, summary="Soumission du QCM")
def submit_qcm_endpoint(
    candidature_id: UUID,
    qcm_submit: QCMSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QCMRead:
    return submit_qcm_for_user(db, candidature_id, user, qcm_submit)


@router.get("/{candidature_id}/qcm/result", response_model=QCMResultRead, summary="Consultation du resultat du QCM")
def get_qcm_result_endpoint(candidature_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> QCMResultRead:
    return get_qcm_result_for_user(db, candidature_id, user)


@router.get("/{candidature_id}/documents", response_model=list[DocumentRead], summary="Liste des documents du dossier")
def list_candidature_documents_endpoint(candidature_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[DocumentRead]:
    return list_documents(db, candidature_id, user)


@router.get("/{candidature_id}/demandes-complement", response_model=list[DemandeComplementRead], summary="Liste des demandes de complement")
def list_demande_complement_endpoint(candidature_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[DemandeComplementRead]:
    return list_demandes_complement(db, candidature_id, user)


@router.post("/{candidature_id}/demandes-complement", response_model=DemandeComplementRead, status_code=status.HTTP_201_CREATED, summary="Creation d'une demande de complement")
def create_demande_complement_endpoint(
    candidature_id: UUID,
    demande: DemandeComplementCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DemandeComplementRead:
    demande_complement = create_demande_complement(db, candidature_id, user, demande)
    return DemandeComplementRead.model_validate(demande_complement)


@router.post("/{candidature_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED, summary="Ajout d'un document au dossier")
async def upload_candidature_document_endpoint(
    candidature_id: UUID,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    document = add_document(db, candidature_id, user, file)
    return DocumentRead.model_validate(document)
