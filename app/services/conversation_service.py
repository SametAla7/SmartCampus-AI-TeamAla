"""Service - Conversations et messages."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import forbidden, not_found
from app.db.session import Session as DBSession
from app.models.conversation import Conversation, Message
from app.models.user import User, UserRole


def create_conversation(db: Session, candidat: User) -> Conversation:
    conversation = Conversation(candidat_id=candidat.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(db: Session, candidat_id: UUID) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.candidat_id == candidat_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def get_conversation_for_user(db: Session, conversation_id: UUID, user: User) -> Conversation:
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise not_found("CONVERSATION_NOT_FOUND", "Conversation introuvable.")
    if user.role != UserRole.ADMINISTRATEUR and conversation.candidat_id != user.id:
        raise forbidden("FORBIDDEN_CONVERSATION_ACCESS", "Acces refuse a cette conversation.")
    return conversation


def create_message(db: Session, conversation: Conversation, sender_id: UUID | None, contenu: str, est_assistant: bool = False) -> Message:
    message = Message(conversation_id=conversation.id, sender_id=sender_id, contenu=contenu)
    # Si le modele a un champ est_assistant, on essaie de le mettre à jour
    try:
        if hasattr(message, "est_assistant"):
            setattr(message, "est_assistant", bool(est_assistant))
    except Exception:
        pass
    conversation.updated_at = datetime.now(timezone.utc)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages(db: Session, conversation_id: UUID) -> list[Message]:
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
