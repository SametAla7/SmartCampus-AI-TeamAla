"""Tests for SMTP email verification."""

import smtplib

from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.user import User
from app.services import email_service


class FakeSMTP:
    instances: list["FakeSMTP"] = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.calls: list[object] = []
        self.message = None
        self.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def ehlo(self):
        self.calls.append("ehlo")

    def starttls(self, context):
        self.calls.append("starttls")

    def login(self, username, password):
        self.calls.append(("login", username, password))

    def send_message(self, message):
        self.message = message
        self.calls.append("send")


def _configure_smtp(monkeypatch) -> None:
    FakeSMTP.instances = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "mailer")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "test-password")
    monkeypatch.setattr(settings, "SMTP_USE_STARTTLS", True)
    monkeypatch.setattr(settings, "SMTP_USE_SSL", False)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)


def test_verification_email_uses_starttls_and_authentication(monkeypatch) -> None:
    _configure_smtp(monkeypatch)

    sent = email_service.send_email_verification_email("Test User", "user@example.com", "signed-token")

    assert sent is True
    smtp = FakeSMTP.instances[0]
    assert smtp.calls == ["ehlo", "starttls", "ehlo", ("login", "mailer", "test-password"), "send"]
    assert smtp.message["To"] == "user@example.com"
    assert "verify_token=signed-token" in smtp.message.get_content()


def test_registration_requires_email_verification_before_login(
    client: TestClient, db_session, monkeypatch
) -> None:
    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "app.api.auth.send_email_verification_email",
        lambda nom, email, token: sent.append((nom, email, token)),
    )

    response = client.post(
        "/api/auth/register",
        json={
            "nom": "Email Test",
            "email": "verify@example.com",
            "mot_de_passe": "password123",
            "role": "CANDIDAT",
        },
    )

    assert response.status_code == 201
    user = db_session.query(User).filter_by(email="verify@example.com").one()
    assert user.email_verified is False
    assert sent and sent[0][1] == user.email

    login = client.post(
        "/api/auth/login",
        json={"email": user.email, "mot_de_passe": "password123"},
    )
    assert login.status_code == 401
    assert login.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"

    verified = client.post("/api/auth/verify-email", json={"token": sent[0][2]})
    assert verified.status_code == 200
    assert db_session.query(User).filter_by(id=user.id).one().email_verified is True
    assert client.post(
        "/api/auth/login",
        json={"email": user.email, "mot_de_passe": "password123"},
    ).status_code == 200


def test_resend_verification_is_generic_for_unknown_email(client: TestClient) -> None:
    response = client.post("/api/auth/resend-verification", json={"email": "unknown@example.com"})

    assert response.status_code == 202
    assert "If this account" in response.json()["message"]
