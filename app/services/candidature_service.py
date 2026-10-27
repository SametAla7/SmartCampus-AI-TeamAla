"""Service - Candidatures (creation, consultation, decisions academiques)."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import bad_request, conflict, forbidden, not_found
from app.db.session import Session as DBSession
from app.models.candidature import Candidature, CandidatureStatut, DecisionCandidature, DecisionCandidatureDecision, QCM
from app.models.entretien import Entretien
from app.models.parcours import Parcours
from app.models.user import User, UserRole
from app.schemas.candidature import (
    CandidatureCreate,
    CandidatureDecision,
    CandidatureListResponse,
    CandidatureRead,
    DecisionCandidatureEnum,
    DecisionCandidatureRead,
)
from app.schemas.parcours import ParcoursRead
from app.schemas.qcm import QCMRead, QCMResultRead, QCMSubmit
from app.schemas.entretien import DemandeComplementRead


def _resolve_default_responsable_academique_id() -> Optional[UUID]:
    if not settings.DEFAULT_RESPONSABLE_ACADEMIQUE_ID:
        return None
    try:
        return UUID(settings.DEFAULT_RESPONSABLE_ACADEMIQUE_ID)
    except (ValueError, TypeError):
        return None


def create_candidature(db: Session, candidat: User, data: CandidatureCreate) -> Candidature:
    parcours = db.query(Parcours).filter(Parcours.id == data.parcours_id).first()
    if parcours is None:
        raise not_found("PARCOURS_NOT_FOUND", "Parcours introuvable.")
    candidature = Candidature(
        candidat_id=candidat.id,
        parcours_id=parcours.id,
        statut=CandidatureStatut.EN_ATTENTE,
        responsable_academique_id=_resolve_default_responsable_academique_id(),
    )
    db.add(candidature)
    db.commit()
    db.refresh(candidature)
    return candidature


def get_candidature(db: Session, candidature_id: UUID) -> Candidature:
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if candidature is None:
        raise not_found("CANDIDATURE_NOT_FOUND", "Candidature introuvable.")
    return candidature


def can_access_candidature(db: Session, user: User, candidature: Candidature) -> bool:
    """Verifie l'acces a un dossier selon le role de l'utilisateur connecte."""
    if user.role == UserRole.ADMINISTRATEUR:
        return True
    if user.role == UserRole.CANDIDAT:
        return candidature.candidat_id == user.id
    if user.role == UserRole.RESPONSABLE_ACADEMIQUE:
        return candidature.responsable_academique_id == user.id
    if user.role == UserRole.RESPONSABLE_ENTRETIEN:
        entretien = (
            db.query(Entretien)
            .filter(Entretien.candidature_id == candidature.id, Entretien.responsable_entretien_id == user.id)
            .first()
        )
        return entretien is not None
    return False


def get_candidature_for_user(db: Session, candidature_id: UUID, user: User) -> Candidature:
    candidature = get_candidature(db, candidature_id)
    if not can_access_candidature(db, user, candidature):
        raise forbidden("FORBIDDEN_CANDIDATURE_ACCESS", "Acces refuse a cette candidature.")
    return candidature


def to_candidature_read(db: Session, candidature: Candidature) -> CandidatureRead:
    return _to_read(candidature)


def list_candidatures(
    db: Session,
    user: User,
    statut: Optional[str] = None,
    parcours_id: Optional[UUID] = None,
    page: int = 1,
    limit: int = 20,
) -> CandidatureListResponse:
    query = db.query(Candidature)
    if user.role == UserRole.CANDIDAT:
        query = query.filter(Candidature.candidat_id == user.id)
    elif user.role == UserRole.RESPONSABLE_ACADEMIQUE:
        query = query.filter(Candidature.responsable_academique_id == user.id)
    elif user.role != UserRole.ADMINISTRATEUR:
        raise forbidden("FORBIDDEN_LIST", "Cette liste n'est pas accessible pour votre role.")

    if statut is not None:
        query = query.filter(Candidature.statut == statut)
    if parcours_id is not None:
        query = query.filter(Candidature.parcours_id == parcours_id)

    total = query.count()
    offset = (page - 1) * limit
    candidatures = query.order_by(Candidature.date_depot.desc()).offset(offset).limit(limit).all()

    items = [CandidatureRead.model_validate(c) for c in candidatures]
    return CandidatureListResponse(items=items, total=total, page=page, limit=limit)


def _latest_decision(candidature: Candidature) -> Optional[DecisionCandidatureRead]:
    decisions = sorted(candidature.decisions or [], key=lambda d: d.date_decision, reverse=True)
    if not decisions:
        return None
    d = decisions[0]
    return DecisionCandidatureRead(
        id=d.id,
        candidature_id=d.candidature_id,
        decision=DecisionCandidatureEnum(d.decision.value),
        commentaire=d.commentaire,
        decisionne_par_id=d.decisionne_par_id,
        date_decision=d.date_decision,
        parcours_destination_id=d.parcours_destination_id,
    )


def _to_read(candidature: Candidature) -> CandidatureRead:
    return CandidatureRead(
        id=candidature.id,
        candidat_id=candidature.candidat_id,
        parcours=ParcoursRead.model_validate(candidature.parcours),
        date_depot=candidature.date_depot,
        statut=candidature.statut,
        responsable_academique_id=candidature.responsable_academique_id,
        decision=_latest_decision(candidature),
    )

def decide_candidature(
    db: Session,
    candidature_id: UUID,
    user: User,
    decision: DecisionCandidatureEnum,
    commentaire: Optional[str] = None,
    parcours_destination_id: Optional[UUID] = None,
) -> CandidatureRead:
    candidature = get_candidature(db, candidature_id)

    is_responsable = user.role == UserRole.RESPONSABLE_ACADEMIQUE
    is_admin = user.role == UserRole.ADMINISTRATEUR
    if not is_responsable and not is_admin:
        raise forbidden("FORBIDDEN_DECISION", "Seul un responsable academique peut prendre une decision.")
    if candidature.statut != CandidatureStatut.EN_ATTENTE:
        raise conflict("CANDIDATURE_NOT_EN_ATTENTE", "Une decision ne peut etre prise que sur une candidature en attente.")

    if decision == DecisionCandidatureEnum.REORIENTER:
        if parcours_destination_id is None:
            raise bad_request("REORIENTATION_REQUIRED", "Une parcours de destination est requis pour une reorientation.")
        parcours_destination = db.query(Parcours).filter(Parcours.id == parcours_destination_id).first()
        if parcours_destination is None:
            raise not_found("PARCOURS_NOT_FOUND", "Parcours de destination introuvable.")
        if parcours_destination_id == candidature.parcours_id:
            raise bad_request("REORIENTATION_SAME_PARCOURS", "Le parcours de destination doit etre different du parcours actuel.")

    decision_entity = DecisionCandidature(
        candidature_id=candidature.id,
        decision=DecisionCandidatureDecision(decision.value),
        commentaire=commentaire,
        decisionne_par_id=user.id,
        parcours_destination_id=parcours_destination_id,
    )
    db.add(decision_entity)

    if decision == DecisionCandidatureEnum.ACCEPTER:
        candidature.statut = CandidatureStatut.VALIDEE
    elif decision == DecisionCandidatureEnum.REJETER:
        candidature.statut = CandidatureStatut.REJETEE
    elif decision == DecisionCandidatureEnum.REORIENTER:
        candidature.statut = CandidatureStatut.REORIENTEE
    else:  # pragma: no cover - defensive
        raise bad_request("DECISION_INVALID", "Decision academique invalide.")

    db.commit()
    db.refresh(decision_entity)
    db.refresh(candidature)
    return _to_read(candidature)


def get_qcm_for_user(db: Session, candidature_id: UUID, user: User) -> QCM:
    """Consultation du QCM associe a une candidature (candidat / responsable)."""
    get_candidature_for_user(db, candidature_id, user)
    qcm = db.query(QCM).filter(QCM.candidature_id == candidature_id).first()
    if qcm is None:
        raise not_found("QCM_NOT_FOUND", "Aucun QCM n'est associe a cette candidature.")
    return qcm


def submit_qcm_for_user(db: Session, candidature_id: UUID, user: User, data: QCMSubmit) -> QCM:
    """Soumission du QCM : au plus un passage par candidature, score fige."""
    candidature = get_candidature_for_user(db, candidature_id, user)
    existing = db.query(QCM).filter(QCM.candidature_id == candidature_id).first()
    if existing is not None:
        raise conflict("QCM_ALREADY_SUBMITTED", "Un seul QCM peut etre passe par candidature.")
    qcm = QCM(candidature_id=candidature_id, score=data.score, date=datetime.now(timezone.utc))
    db.add(qcm)
    db.commit()
    db.refresh(qcm)
    return qcm


def get_qcm_result_for_user(db: Session, candidature_id: UUID, user: User) -> QCMResultRead:
    qcm = get_qcm_for_user(db, candidature_id, user)
    return QCMResultRead(score=qcm.score, date=qcm.date)
