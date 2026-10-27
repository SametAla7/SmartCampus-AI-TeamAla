"""Service - Chatbot (integration LLM / RAG preparee, non operationnelle par defaut)."""

from app.core.config import settings
from app.core.errors import service_unavailable
from app.db.session import Session
from app.models.conversation import Conversation


class ChatbotNotConfiguredError(Exception):
    """Le chatbot n'est pas encore configure (provider LLM / RAG indisponible)."""


def is_chatbot_configured() -> bool:
    return bool(settings.CHATBOT_ENABLED and settings.CHATBOT_PROVIDER and settings.CHATBOT_API_KEY)


def generate_reply(conversation: Conversation, contenu: str) -> str:
    """Genere une reponse du chatbot.

    Ne simule JAMAIS une reponse : si aucun provider LLM ni systeme RAG n'est
    configure, une erreur explicite est renvoyee au client.
    """
    if not is_chatbot_configured():
        raise service_unavailable("CHATBOT_NOT_CONFIGURED", "Le chatbot n'est pas configure pour le moment.")
    # Integration LLM / RAG a prevoir : retrieval documentaire + generation.
    return "reponse du chatbot"
