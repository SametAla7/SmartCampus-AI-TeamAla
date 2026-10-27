"""Modeles SQLAlchemy - Candidature, DecisionCandidature (extension) et QCM."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.parcours import Parcours
from app.models.user import User


class CandidatureStatut(str, Enum):
    """Jeu de caracteres controle des statuts de candidature."""

    EN_ATTENTE = "EN_ATTENTE"
    VALIDEE = "VALIDEE"
    REJETEE = "REJETEE"
    REORIENTEE = "REORIENTEE"


class DecisionCandidatureDecision(str, Enum):
    """Decisions academiques possibles prises par un responsable academique."""

    ACCEPTER = "ACCEPTER"
    REJETER = "REJETER"
    REORIENTER = "REORIENTER"


class Candidature(Base):
    """Dossier de candidature depose par un candidat pour un parcours."""

    __tablename__ = "candidatures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidat_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parcours_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("parcours.id", ondelete="CASCADE"), nullable=False)
    date_depot: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    statut: Mapped[CandidatureStatut] = mapped_column(SAEnum(CandidatureStatut, name="candidature_statut"), nullable=False, default=CandidatureStatut.EN_ATTENTE)
    responsable_academique_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    candidat: Mapped[User] = relationship(foreign_keys=[candidat_id])
    parcours: Mapped[Parcours] = relationship(back_populates="candidatures", foreign_keys=[parcours_id])
    decisions: Mapped[list["DecisionCandidature"]] = relationship(back_populates="candidature", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="candidature", cascade="all, delete-orphan")
    demandes_complement: Mapped[list["DemandeComplement"]] = relationship(back_populates="candidature", cascade="all, delete-orphan")
    entretien: Mapped[Optional["Entretien"]] = relationship(back_populates="candidature", uselist=False)
    qcm: Mapped[Optional["QCM"]] = relationship(back_populates="candidature", uselist=False)

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<Candidature id={self.id} statut={self.statut}>"


class DecisionCandidature(Base):
    """Historique des decisions academiques (extension technique du diagramme).

    Le diagramme UML initial ne descrive pas explicitement cet etre ; il est
    ajoute pour tracer les decisions de validation (accepter / rejeter /
    reorienter) de facon traçable.
    """

    __tablename__ = "decision_candidatures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidature_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False)
    decision: Mapped[DecisionCandidatureDecision] = mapped_column(
        SAEnum(DecisionCandidatureDecision, name="decision_candidature_decision"), nullable=False
    )
    commentaire: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decisionne_par_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    date_decision: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    parcours_destination_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("parcours.id", ondelete="SET NULL"), nullable=True)

    candidature: Mapped[Candidature] = relationship(back_populates="decisions")
    decisionne_par: Mapped[Optional[User]] = relationship(back_populates="decisions")

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<DecisionCandidature id={self.id} decision={self.decision}>"


class QCM(Base):
    """Questionnaire QCM associe a une candidature (au plus un par candidature)."""

    __tablename__ = "qcms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidature_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False, unique=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    candidature: Mapped[Candidature] = relationship(back_populates="qcm", uselist=False)

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<QCM id={self.id} candidature_id={self.candidature_id} score={self.score}>"
