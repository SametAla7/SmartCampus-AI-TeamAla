"""Routes - Conversations et messages du chatbot."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.core.errors import forbidden, service_unavailable
from app.db.session import Session, get_db
from app.models.user import User, UserRole
from app.schemas.conversation import ConversationDetailResponse, ConversationRead, MessageCreate, MessageRead
from app.services import chatbot_service
from app.services.conversation_service import (
    create_conversation,
    create_message,
    get_conversation_for_user,
    list_messages,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED, summary="Creation d'une conversation candidat / chatbot")
def create_conversation_endpoint(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConversationRead:
    if user.role != UserRole.CANDIDAT:
        raise forbidden("FORBIDDEN_ROLE", "Seuls les candidats peuvent creer des conversations avec le chatbot.")
    conversation = create_conversation(db, user)
    return ConversationRead.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse, summary="Consultation d'une conversation (candidat proprietaire ou admin)")
def get_conversation_endpoint(conversation_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConversationDetailResponse:
    conversation = get_conversation_for_user(db, conversation_id, user)
    messages = list_messages(db, conversation.id)
    return ConversationDetailResponse(
        id=conversation.id,
        candidat_id=conversation.candidat_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageRead.model_validate(m) for m in messages],
    )


@router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED, summary="Envoi d'un message au chatbot")
def send_message_endpoint(
    conversation_id: UUID,
    message_create: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    conversation = get_conversation_for_user(db, conversation_id, user)
    if not chatbot_service.is_chatbot_configured():
        raise service_unavailable("CHATBOT_NOT_CONFIGURED", "Le chatbot n'est pas configure pour le moment.")
    sent_message = create_message(db, conversation, user.id, message_create.contenu)
    reply = chatbot_service.generate_reply(conversation, message_create.contenu)
    if reply:
        create_message(db, conversation, None, reply, est_assistant=True)
    return MessageRead.model_validate(sent_message)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead], summary="Historique des messages")
def list_messages_endpoint(conversation_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[MessageRead]:
    conversation = get_conversation_for_user(db, conversation_id, user)
    messages = list_messages(db, conversation.id)
    return [MessageRead.model_validate(m) for m in messages]
