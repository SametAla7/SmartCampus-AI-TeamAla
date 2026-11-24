"""HTTP client for the independent Colab LLM inference API."""

import logging

import httpx

from app.core.config import settings
from app.core.errors import APIError, service_unavailable

logger = logging.getLogger(__name__)


def generate_answer(message: str, history: list[dict[str, str]], language: str | None = None) -> str:
    """Call the configured inference endpoint and return its generated answer."""
    base_url = (settings.COLAB_INFERENCE_URL or "").strip().rstrip("/")
    if not base_url:
        raise service_unavailable("CHATBOT_NOT_CONFIGURED", "Le chatbot Colab n'est pas configure.")

    endpoint = settings.COLAB_INFERENCE_CHAT_ENDPOINT.strip()
    url = f"{base_url}/{endpoint.lstrip('/')}"
    headers = {}
    api_key = (settings.COLAB_INFERENCE_API_KEY or "").strip()
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = httpx.post(
            url,
            json={"message": message, "history": history, "language": language},
            headers=headers,
            timeout=settings.COLAB_INFERENCE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        result = response.json()
    except httpx.TimeoutException as exc:
        logger.warning("Colab inference request timed out")
        raise service_unavailable(
            "CHATBOT_TIMEOUT",
            "Le service du chatbot met trop de temps a repondre. Veuillez reessayer.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning("Colab inference returned HTTP %s", exc.response.status_code)
        if exc.response.status_code >= 500:
            raise service_unavailable(
                "CHATBOT_UPSTREAM_UNAVAILABLE",
                "Le service du chatbot est temporairement indisponible.",
            ) from exc
        raise APIError(
            502,
            "CHATBOT_UPSTREAM_ERROR",
            "Le service du chatbot a refuse la requete.",
        ) from exc
    except httpx.RequestError as exc:
        logger.warning("Could not connect to Colab inference service: %s", type(exc).__name__)
        raise service_unavailable(
            "CHATBOT_UPSTREAM_UNAVAILABLE",
            "Impossible de joindre le service du chatbot. Verifiez que le serveur Colab est actif.",
        ) from exc
    except (ValueError, TypeError) as exc:
        logger.exception("Colab inference returned an invalid response")
        raise APIError(502, "CHATBOT_INVALID_RESPONSE", "Le service du chatbot a retourne une reponse invalide.") from exc

    answer = result.get("answer") if isinstance(result, dict) and result.get("success") is True else None
    if not isinstance(answer, str) or not answer.strip():
        logger.error("Colab inference response did not contain a successful non-empty answer")
        raise APIError(502, "CHATBOT_INVALID_RESPONSE", "Le service du chatbot a retourne une reponse invalide.")
    return answer.strip()
