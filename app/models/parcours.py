"""Modeles SQLAlchemy - Parcours."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParcoursEtablissement(str, Enum):
    """Etablissement d'appartenance d'un parcours (IIT / ISB)."""

    IIT = "IIT"
    ISB = "ISB"


class Parcours(Base):
    """Un parcours academique propose par l'IIT ou l'ISB."""

    __tablename__ = "parcours"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    etablissement: Mapped[ParcoursEtablissement] = mapped_column(
        SAEnum(ParcoursEtablissement, name="parcours_etablissement"), nullable=False, default=ParcoursEtablissement.IIT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    candidatures: Mapped[list["Candidature"]] = relationship(back_populates="parcours", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<Parcours id={self.id} nom={self.nom} etablissement={self.etablissement}>"
