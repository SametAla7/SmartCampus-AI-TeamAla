"""Modeles SQLAlchemy - Utilisateur et roles."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Uuid, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, Enum):
    """Roles de la plateforme (specialisations de Utilisateur)."""

    CANDIDAT = "CANDIDAT"
    RESPONSABLE_ACADEMIQUE = "RESPONSABLE_ACADEMIQUE"
    RESPONSABLE_ENTRETIEN = "RESPONSABLE_ENTRETIEN"
    DIRECTION = "DIRECTION"
    ADMINISTRATEUR = "ADMINISTRATEUR"


class User(Base):
    """Classe de base commune aux profils de la plateforme.

    Table unique `users` : les donnees communes (identite, hash du mot de
    passe, role, compte actif) sont stockees ici. Les profils specialises
    (Candidat, Responsable Academique, Responsable d'Entretien, Direction,
    Administrateur) sont representes par le champ `role` assocue aux
    entites metier, sans duplication inutile des donnees communes.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    password_set: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="candidat", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["DecisionCandidature"]] = relationship(back_populates="decisionne_par", cascade="all, delete-orphan")
    demandes_complement: Mapped[list["DemandeComplement"]] = relationship(back_populates="demande_par", cascade="all, delete-orphan")
    entretiens: Mapped[list["Entretien"]] = relationship(back_populates="responsable_entretien", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<User id={self.id} email={self.email} role={self.role}>"
