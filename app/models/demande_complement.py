"""Modeles SQLAlchemy - DemandeComplement (extension du diagramme UML)."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.candidature import Candidature
from app.models.user import User


class DemandeComplementStatut(str, Enum):
    """Statuts d'une demande de complement d'information / document."""

    EN_ATTENTE = "EN_ATTENTE"
    TRAITEE = "TRAITEE"


class DemandeComplement(Base):
    """Demande de complement d'information ou de document (extension UML).

    Le diagramme de cas d'utilisation ne definit pas d'entite dediee pour cette
    fonctionnalite ; elle est ajoutee comme extension technique.
    """

    __tablename__ = "demandes_complement"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidature_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False, index=True)
    contenu: Mapped[str] = mapped_column(String(3000), nullable=False)
    informations_attendues: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    type_document: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    statut: Mapped[DemandeComplementStatut] = mapped_column(SAEnum(DemandeComplementStatut, name="demande_complement_statut"), nullable=False, default=DemandeComplementStatut.EN_ATTENTE)
    date_demande: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    demande_par_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    candidature: Mapped[Candidature] = relationship(back_populates="demandes_complement")
    demande_par: Mapped[Optional[User]] = relationship(back_populates="demandes_complement")

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<DemandeComplement id={self.id} candidature_id={self.candidature_id} statut={self.statut}>"
