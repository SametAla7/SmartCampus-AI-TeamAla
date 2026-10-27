"""Service - Parcours academiques (consultation candidat / administration simple)."""

from uuid import UUID

from app.core.errors import not_found
from app.db.session import Session
from app.models.parcours import Parcours, ParcoursEtablissement
from app.schemas.parcours import ParcoursEtablissementEnum, ParcoursListResponse, ParcoursRead


def list_parcours(db: Session, etablissement: str | None = None) -> ParcoursListResponse:
    query = db.query(Parcours)
    if etablissement is not None:
        try:
            etablissement_enum = ParcoursEtablissementEnum(etablissement)
        except ValueError:
            raise not_found("PARCOURS_ETABLISSEMENT_INVALID", f"Etablissement inconnu : {etablissement}.")
        query = query.filter(Parcours.etablissement == etablissement_enum)
    parcours_list = query.order_by(Parcours.nom).all()
    return ParcoursListResponse(items=[ParcoursRead.model_validate(p) for p in parcours_list])


def get_parcours(db: Session, parcours_id: UUID) -> Parcours:
    parcours = db.query(Parcours).filter(Parcours.id == parcours_id).first()
    if parcours is None:
        raise not_found("PARCOURS_NOT_FOUND", "Parcours introuvable.")
    return parcours
