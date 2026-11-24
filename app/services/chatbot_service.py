"""Application-level conversation adapter for the Colab inference client."""

from app.core.config import settings
from app.core.errors import service_unavailable
from app.models.conversation import Conversation, Message
from app.services.colab_inference_client import generate_answer


def is_chatbot_configured() -> bool:
    return bool(settings.CHATBOT_ENABLED and (settings.COLAB_INFERENCE_URL or "").strip())


def generate_reply(
    conversation: Conversation,
    contenu: str,
    history: list[Message] | None = None,
    language: str | None = None,
) -> str:
    """Forward a message and recent conversation turns to the configured model."""
    if not is_chatbot_configured():
        raise service_unavailable("CHATBOT_NOT_CONFIGURED", "Le chatbot Colab n'est pas configure.")
    history_limit = max(settings.COLAB_INFERENCE_HISTORY_LIMIT, 0)
    recent_history = (history or [])[-history_limit:] if history_limit else []
    history_payload = [
        {
            "role": "assistant" if message.est_assistant else "user",
            "content": message.contenu,
        }
        for message in recent_history
    ]
    return generate_answer(contenu, history_payload, language)
