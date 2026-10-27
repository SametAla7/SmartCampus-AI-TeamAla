"""Schema Pydantic - Conversation, Message et QCM."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    pass


class ConversationRead(BaseModel):
    id: UUID
    candidat_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    contenu: str = Field(..., min_length=1, max_length=5000)


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID | None = None
    contenu: str
    est_assistant: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    id: UUID
    candidat_id: UUID
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRead]
