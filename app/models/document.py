"""Modeles SQLAlchemy - Document."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.candidature import Candidature


class Document(Base):
    """Un document rattache a une candidature.

    Le contenu binaire n'est pas stocke en base : seuls les metadonnees
    (nom, type, taille, stockage) sont persistees. Le stockage binaire
    utilise une solution de stockage adaptee (systeme de fichiers local en
    developpement, bucket S3-compatible en production).
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidature_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("candidatures.id", ondelete="CASCADE"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    taille_octets: Mapped[int] = mapped_column(Integer, nullable=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    date_ajout: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    candidature: Mapped[Candidature] = relationship(back_populates="documents")

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<Document id={self.id} candidature_id={self.candidature_id} nom={self.nom}>"
