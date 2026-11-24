from types import SimpleNamespace

import httpx
import pytest

from app.core.config import settings
from app.core.errors import APIError
from app.services import colab_inference_client


def _configure_inference(monkeypatch) -> None:
    monkeypatch.setattr(settings, "CHATBOT_ENABLED", True)
    monkeypatch.setattr(settings, "COLAB_INFERENCE_URL", "https://example.ngrok.app/")
    monkeypatch.setattr(settings, "COLAB_INFERENCE_CHAT_ENDPOINT", "/chat")
    monkeypatch.setattr(settings, "COLAB_INFERENCE_API_KEY", "test-api-key")
    monkeypatch.setattr(settings, "COLAB_INFERENCE_TIMEOUT_SECONDS", 45)
    monkeypatch.setattr(settings, "COLAB_INFERENCE_HISTORY_LIMIT", 20)


def test_client_maps_messages_to_colab_contract(monkeypatch) -> None:
    _configure_inference(monkeypatch)
    captured = {}

    class Response:
        def raise_for_status(self):
            pass

        @staticmethod
        def json():
            return {"success": True, "answer": "Welcome!"}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()

    monkeypatch.setattr(colab_inference_client.httpx, "post", fake_post)
    history = [
        SimpleNamespace(est_assistant=False, contenu="Hello"),
        SimpleNamespace(est_assistant=True, contenu="Hi, how can I help?"),
    ]

    answer = colab_inference_client.generate_answer(
        "Which programs are available?",
        history=[
            {"role": "assistant" if message.est_assistant else "user", "content": message.contenu}
            for message in history
        ],
        language="en",
    )

    assert answer == "Welcome!"
    assert captured["url"] == "https://example.ngrok.app/chat"
    assert captured["headers"] == {"X-API-Key": "test-api-key"}
    assert captured["timeout"] == 45
    assert captured["json"] == {
        "message": "Which programs are available?",
        "history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi, how can I help?"},
        ],
        "language": "en",
    }


def test_generate_reply_reports_timeout_as_service_unavailable(monkeypatch) -> None:
    _configure_inference(monkeypatch)

    def timeout(*args, **kwargs):
        request = httpx.Request("POST", "https://example.ngrok.app/chat")
        raise httpx.ReadTimeout("upstream timed out", request=request)

    monkeypatch.setattr(colab_inference_client.httpx, "post", timeout)

    with pytest.raises(APIError) as error:
        colab_inference_client.generate_answer("Hello", [])

    assert error.value.status_code == 503
    assert error.value.error_code == "CHATBOT_TIMEOUT"


def test_generate_reply_rejects_unsuccessful_or_empty_upstream_response(monkeypatch) -> None:
    _configure_inference(monkeypatch)

    class Response:
        def raise_for_status(self):
            pass

        @staticmethod
        def json():
            return {"success": True, "answer": "  "}

    monkeypatch.setattr(colab_inference_client.httpx, "post", lambda *args, **kwargs: Response())

    with pytest.raises(APIError) as error:
        colab_inference_client.generate_answer("Hello", [])

    assert error.value.status_code == 502
    assert error.value.error_code == "CHATBOT_INVALID_RESPONSE"
