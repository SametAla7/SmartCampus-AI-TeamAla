"""Service - Entretiens et demandes de complement."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import bad_request, conflict, forbidden, not_found
from app.db.session import Session as DBSession
from app.models.candidature import Candidature
from app.models.demande_complement import DemandeComplement, DemandeComplementStatut
from app.models.entretien import Entretien
from app.models.user import User, UserRole
from app.schemas.entretien import DemandeComplementCreate, DemandeComplementRead, EntretienApproval, EntretienCreate, EntretienRead
from app.services.candidature_service import can_access_candidature


def create_entretien(db: Session, candidature_id: UUID, user: User, data: EntretienCreate) -> Entretien:
    if user.role != UserRole.RESPONSABLE_ENTRETIEN and user.role != UserRole.ADMINISTRATEUR:
        raise forbidden("FORBIDDEN_ROLE", "Seul un responsable d'entretien peut organiser un entretien.")
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if candidature is None:
        raise not_found("CANDIDATURE_NOT_FOUND", "Candidature introuvable.")
    existing = db.query(Entretien).filter(Entretien.candidature_id == candidature_id).first()
    if existing is not None:
        raise conflict("ENTRETIEN_ALREADY_EXISTS", "Une candidature ne peut avoir qu'un seul entretien.")
    entretien = Entretien(
        candidature_id=candidature_id,
        responsable_entretien_id=user.id,
        date=data.date,
        approuve=False,
    )
    db.add(entretien)
    db.commit()
    db.refresh(entretien)
    return entretien


def get_entretien(db: Session, entretien_id: UUID) -> Entretien:
    entretien = db.query(Entretien).filter(Entretien.id == entretien_id).first()
    if entretien is None:
        raise not_found("ENTRETIEN_NOT_FOUND", "Entretien introuvable.")
    return entretien


def list_entretiens(db: Session, user: User) -> list[Entretien]:
    if user.role == UserRole.CANDIDAT:
        return db.query(Entretien).join(Candidature, Candidature.id == Entretien.candidature_id).filter(Candidature.candidat_id == user.id).all()
    if user.role == UserRole.RESPONSABLE_ACADEMIQUE:
        return db.query(Entretien).join(Candidature, Candidature.id == Entretien.candidature_id).filter(Candidature.responsable_academique_id == user.id).all()
    if user.role == UserRole.RESPONSABLE_ENTRETIEN:
        return db.query(Entretien).filter(Entretien.responsable_entretien_id == user.id).all()
    raise forbidden("FORBIDDEN_LIST", "Cette liste n'est pas accessible pour votre role.")


def approve_entretien(db: Session, entretien_id: UUID, user: User, data: EntretienApproval) -> Entretien:
    entretien = get_entretien(db, entretien_id)
    if user.role != UserRole.RESPONSABLE_ENTRETIEN and user.role != UserRole.ADMINISTRATEUR:
        raise forbidden("FORBIDDEN_APPROVAL", "Seul un responsable d'entretien peut enregistrer une approbation.")
    if user.id != entretien.responsable_entretien_id and user.role != UserRole.ADMINISTRATEUR:
        raise forbidden("FORBIDDEN_APPROVAL", "Vous n'etes pas le responsable de cet entretien.")
    if entretien.approuve and not data.approuve:
        raise conflict("ENTRETIEN_ALREADY_APPROVED", "Une approbation d'entretien ne peut plus etre modifiee.")
    if data.approuve:
        entretien.approuve = True
        db.commit()
        db.refresh(entretien)
    return entretien


def create_demande_complement(db: Session, candidature_id: UUID, user: User, data: DemandeComplementCreate) -> DemandeComplement:
    if user.role != UserRole.RESPONSABLE_ENTRETIEN and user.role != UserRole.ADMINISTRATEUR:
        raise forbidden("FORBIDDEN_DEMANDE_COMPLEMENT", "Seul un responsable d'entretien peut demander un complement.")
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if candidature is None:
        raise not_found("CANDIDATURE_NOT_FOUND", "Candidature introuvable.")
    demande = DemandeComplement(
        candidature_id=candidature_id,
        contenu=data.contenu,
        informations_attendues=data.informations_attendues,
        type_document=data.type_document,
        statut=DemandeComplementStatut.EN_ATTENTE,
        demande_par_id=user.id,
    )
    db.add(demande)
    db.commit()
    db.refresh(demande)
    return demande


def list_demandes_complement(db: Session, candidature_id: UUID, user: User) -> list[DemandeComplementRead]:
    """Liste les demandes de complement d'information / documents d'une candidature."""
    from app.models.candidature import Candidature as CandidatureModel

    candidature = db.query(CandidatureModel).filter(CandidatureModel.id == candidature_id).first()
    if candidature is None:
        raise not_found("CANDIDATURE_NOT_FOUND", "Candidature introuvable.")
    if not can_access_candidature(db, user, candidature):
        raise forbidden("FORBIDDEN_DEMANDE_COMPLEMENT", "Acces refuse a cette demande.")
    demandes = (
        db.query(DemandeComplement)
        .filter(DemandeComplement.candidature_id == candidature_id)
        .order_by(DemandeComplement.date_demande.desc())
        .all()
    )
    return [DemandeComplementRead.model_validate(d) for d in demandes]
