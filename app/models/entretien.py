"""Modeles SQLAlchemy - Entretien."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.candidature import Candidature
from app.models.user import User


class Entretien(Base):
    """Un entretien organise pour une candidature (zéro ou un par candidature)."""

    __tablename__ = "entretiens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidature_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    responsable_entretien_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approuve: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    candidature: Mapped[Candidature] = relationship(back_populates="entretien")
    responsable_entretien: Mapped[User] = relationship(back_populates="entretiens")

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<Entretien id={self.id} candidature_id={self.candidature_id} approuve={self.approuve}>"
