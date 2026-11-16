"""Tests - SMTP (service d'email) et reinitialisation de mot de passe."""

import smtplib

import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.core.config import settings
from app.services import email_service
from tests.conftest import create_user, login_payload


@pytest.fixture()
def sent_reset_emails(monkeypatch) -> list:
    sent: list = []
    monkeypatch.setattr("app.api.auth.send_password_reset_email", lambda nom, email, token: sent.append((nom, email, token)))
    return sent


class FakeSMTP:
    instances: list = []

    def __init__(self, host, port, timeout=None, context=None):
        self.host, self.port, self.context = host, port, context
        self.calls: list = []
        self.sent = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def ehlo(self):
        self.calls.append("ehlo")

    def starttls(self, context=None):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(("login", user))

    def send_message(self, message):
        self.sent = message


def _configure_smtp(monkeypatch) -> None:
    FakeSMTP.instances = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "mailer")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@smartcampus.test")
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)


def test_send_email_returns_false_when_smtp_not_configured() -> None:
    assert email_service.send_email("a@test.com", "Sujet", "Corps") is False


def test_send_email_uses_starttls_login_and_sends(monkeypatch) -> None:
    _configure_smtp(monkeypatch)
    assert email_service.send_email("dest@test.com", "Sujet", "Corps", "<p>Corps</p>") is True
    server = FakeSMTP.instances[0]
    assert server.calls == ["ehlo", "starttls", "ehlo", ("login", "mailer")]
    assert server.sent["To"] == "dest@test.com"
    assert server.sent["Subject"] == "Sujet"
    assert "noreply@smartcampus.test" in server.sent["From"]


def test_send_email_returns_false_on_smtp_error(monkeypatch) -> None:
    _configure_smtp(monkeypatch)

    class Failing(FakeSMTP):
        def send_message(self, message):
            raise smtplib.SMTPRecipientsRefused({})

    monkeypatch.setattr(smtplib, "SMTP", Failing)
    assert email_service.send_email("dest@test.com", "Sujet", "Corps") is False


def test_register_sends_welcome_email(client: TestClient, monkeypatch) -> None:
    welcomed: list = []
    monkeypatch.setattr("app.api.auth.send_welcome_email", lambda nom, email: welcomed.append((nom, email)))
    response = client.post(
        "/api/auth/register", json={"nom": "Nouveau Candidat", "email": "nouveau@test.com", "mot_de_passe": "password123"}
    )
    assert response.status_code == 201
    assert welcomed == [("Nouveau Candidat", "nouveau@test.com")]


def test_register_succeeds_even_if_smtp_unconfigured(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register", json={"nom": "Nouveau Candidat", "email": "nouveau@test.com", "mot_de_passe": "password123"}
    )
    assert response.status_code == 201


def test_forgot_password_unknown_email_same_answer_no_email(client: TestClient, sent_reset_emails) -> None:
    response = client.post("/api/auth/forgot-password", json={"email": "inconnu@test.com"})
    assert response.status_code == 202
    assert sent_reset_emails == []


def test_forgot_password_known_email_sends_and_answers_identically(
    client: TestClient, db_session, sent_reset_emails
) -> None:
    create_user(db_session, "Candidat Test", "candidat@test.com")
    unknown = client.post("/api/auth/forgot-password", json={"email": "inconnu@test.com"})
    known = client.post("/api/auth/forgot-password", json={"email": "Candidat@Test.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(sent_reset_emails) == 1
    assert sent_reset_emails[0][1] == "candidat@test.com"


def test_forgot_password_inactive_account_sends_nothing(client: TestClient, db_session, sent_reset_emails) -> None:
    create_user(db_session, "Inactif", "inactif@test.com", est_actif=False)
    response = client.post("/api/auth/forgot-password", json={"email": "inactif@test.com"})
    assert response.status_code == 202
    assert sent_reset_emails == []


def test_reset_password_flow_and_single_use(client: TestClient, db_session, sent_reset_emails) -> None:
    create_user(db_session, "Candidat Test", "candidat@test.com", password="ancienmdp123")
    client.post("/api/auth/forgot-password", json={"email": "candidat@test.com"})
    token = sent_reset_emails[0][2]

    ok = client.post("/api/auth/reset-password", json={"token": token, "nouveau_mot_de_passe": "nouveaumdp456"})
    assert ok.status_code == 200

    assert login_payload(client, "candidat@test.com", "nouveaumdp456")["user"]["email"] == "candidat@test.com"
    old = client.post("/api/auth/login", json={"email": "candidat@test.com", "mot_de_passe": "ancienmdp123"})
    assert old.status_code == 401

    reuse = client.post("/api/auth/reset-password", json={"token": token, "nouveau_mot_de_passe": "autremdp7890"})
    assert reuse.status_code == 401
    assert reuse.json()["error"]["code"] == "RESET_TOKEN_INVALID"


def test_reset_password_rejects_garbage_and_wrong_token_types(client: TestClient, db_session) -> None:
    user = create_user(db_session, "Candidat Test", "candidat@test.com")
    garbage = client.post("/api/auth/reset-password", json={"token": "pas-un-jwt", "nouveau_mot_de_passe": "nouveaumdp456"})
    assert garbage.status_code == 401

    access = security.create_access_token(user.id, user.role.value)
    wrong_type = client.post("/api/auth/reset-password", json={"token": access, "nouveau_mot_de_passe": "nouveaumdp456"})
    assert wrong_type.status_code == 401
    assert wrong_type.json()["error"]["code"] == "RESET_TOKEN_INVALID"


def test_reset_token_is_not_accepted_as_access_token(client: TestClient, db_session) -> None:
    user = create_user(db_session, "Candidat Test", "candidat@test.com")
    token = security.create_password_reset_token(user.id, user.mot_de_passe)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_reset_password_enforces_min_length(client: TestClient, db_session) -> None:
    user = create_user(db_session, "Candidat Test", "candidat@test.com")
    token = security.create_password_reset_token(user.id, user.mot_de_passe)
    response = client.post("/api/auth/reset-password", json={"token": token, "nouveau_mot_de_passe": "court"})
    assert response.status_code == 422
