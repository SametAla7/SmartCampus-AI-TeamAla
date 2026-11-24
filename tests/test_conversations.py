"""Tests - Conversations et chatbot."""

from uuid import UUID

from fastapi.testclient import TestClient

from app.models.conversation import Conversation
from app.models.user import UserRole
from app.services.conversation_service import create_message
from tests.conftest import create_user, login_payload


def create_candidate_token(client: TestClient, db, email: str = "cand-chat@test.com") -> tuple[dict, object]:
    user = create_user(db, "Candidat", email, role=UserRole.CANDIDAT)
    return login_payload(client, user.email), user


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_conversation(client: TestClient, token: str) -> dict:
    response = client.post("/api/conversations", headers=auth(token))
    assert response.status_code == 201, response.text
    return response.json()


def test_candidate_creates_conversation(client: TestClient, db_session) -> None:
    token_response, _ = create_candidate_token(client, db_session)
    conversation = create_conversation(client, token_response["access_token"])
    assert "id" in conversation

    detail = client.get(f"/api/conversations/{conversation['id']}", headers=auth(token_response["access_token"]))
    assert detail.status_code == 200
    assert detail.json()["messages"] == []


def test_conversation_requires_candidat_role(client: TestClient, db_session, monkeypatch) -> None:
    from app.models.user import User

    admin = create_user(db_session, "Admin", "admin-chat@test.com", password="password123", role=UserRole.ADMINISTRATEUR)
    token_response = login_payload(client, admin.email)
    response = client.post("/api/conversations", headers=auth(token_response["access_token"]))
    assert response.status_code == 403


def test_send_message_without_chatbot_returns_503(client: TestClient, db_session) -> None:
    token_response, _ = create_candidate_token(client, db_session)
    conversation = create_conversation(client, token_response["access_token"])

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        json={"contenu": "Bonjour, je souhaite connaître les parcours."},
        headers=auth(token_response["access_token"]),
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "CHATBOT_NOT_CONFIGURED"


def test_send_message_with_configured_chatbot(client: TestClient, db_session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.chatbot_service.is_chatbot_configured", lambda: True)
    captured = {}

    def generate_reply(conversation, contenu, history=None):
        captured["history"] = history
        return "reponse du chatbot"

    monkeypatch.setattr("app.services.chatbot_service.generate_reply", generate_reply)

    token_response, user = create_candidate_token(client, db_session)
    conversation = create_conversation(client, token_response["access_token"])
    db_conversation = db_session.query(Conversation).filter_by(id=UUID(conversation["id"])).one()
    create_message(db_session, db_conversation, user.id, "Old user message")
    create_message(db_session, db_conversation, None, "Old assistant reply", est_assistant=True)

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        json={"contenu": "Bonjour"},
        headers=auth(token_response["access_token"]),
    )
    assert response.status_code == 201, response.text

    messages_response = client.get(f"/api/conversations/{conversation['id']}/messages", headers=auth(token_response["access_token"]))
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) == 4
    assert messages[-2]["contenu"] == "Bonjour"
    assert messages[-1]["contenu"] == "reponse du chatbot"
    assert messages[-1]["est_assistant"] is True
    assert [(message.contenu, message.est_assistant) for message in captured["history"]] == [
        ("Old user message", False),
        ("Old assistant reply", True),
    ]
