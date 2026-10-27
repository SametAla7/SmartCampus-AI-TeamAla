"""Modeles SQLAlchemy - Conversation et Message."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class Conversation(Base):
    """Une conversation entre un candidat et le chatbot."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidat_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    candidat: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<Conversation id={self.id} candidat_id={self.candidat_id}>"


class Message(Base):
    """Message d'une conversation (extension technique du diagramme UML).

    Le diagramme UML initial ne contenait pas de classe Message ; elle est
    ajoutee comme extension technique pour rendre l'historique de conversation
    reellement exploitable, en attendant une implémentation RAG / LLM.
    """

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    contenu: Mapped[str] = mapped_column(String(5000), nullable=False)
    est_assistant: Mapped[bool] = mapped_column("est_assistant", nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    sender: Mapped[Optional[User]] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - utilitaire de debogage
        return f"<Message id={self.id} conversation_id={self.conversation_id} contenu={self.contenu[:30]}>"
