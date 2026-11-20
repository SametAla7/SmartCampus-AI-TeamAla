"""Tests for Google account creation and first-login password setup."""

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings
from app.main import _ensure_user_auth_columns
from app.models.user import User
from app.services import oauth_service
from tests.conftest import auth_headers


def _configure_google(monkeypatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/google/callback")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:4200")
    monkeypatch.setattr(settings, "APP_ENV", "development")


def _begin_login(client: TestClient) -> str:
    response = client.get("/api/auth/oauth/google/login", follow_redirects=False)
    assert response.status_code == 302
    authorization = parse_qs(urlparse(response.headers["location"]).query)
    return authorization["state"][0]


def _callback(client: TestClient, state: str):
    return client.get(
        "/api/auth/oauth/google/callback",
        params={"code": "authorization-code", "state": state},
        follow_redirects=False,
    )


def test_google_first_login_persists_user_and_requires_password_setup(
    client: TestClient, db_session, monkeypatch
) -> None:
    _configure_google(monkeypatch)
    monkeypatch.setattr(
        oauth_service,
        "fetch_google_profile",
        lambda code: {"sub": "google-user-1", "email": "new.user@example.com", "nom": "New User"},
    )

    callback = _callback(client, _begin_login(client))
    assert callback.status_code == 302
    fragment = parse_qs(urlparse(callback.headers["location"]).fragment)
    assert fragment["requires_password_setup"] == ["true"]

    user = db_session.query(User).filter_by(email="new.user@example.com").one()
    assert user.google_sub == "google-user-1"
    assert user.password_set is False

    token = fragment["access_token"][0]
    assert client.get("/api/auth/me", headers=auth_headers(token)).status_code == 401
    setup = client.post(
        "/api/auth/setup-password",
        json={"mot_de_passe": "new-password-123"},
        headers=auth_headers(token),
    )
    assert setup.status_code == 200
    assert user.password_set is True
    assert client.get("/api/auth/me", headers=auth_headers(token)).status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"email": "new.user@example.com", "mot_de_passe": "new-password-123"},
    )
    assert login.status_code == 200


def test_google_login_url_uses_callback_origin(client: TestClient, monkeypatch) -> None:
    _configure_google(monkeypatch)
    monkeypatch.setattr(
        settings,
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8000/api/auth/oauth/google/callback",
    )

    response = client.get("/api/auth/oauth/providers")

    assert response.status_code == 200
    assert response.json() == {
        "google": True,
        "google_login_url": "http://127.0.0.1:8000/api/auth/oauth/google/login",
    }


def test_google_repeat_login_reuses_account_without_setup(client: TestClient, db_session, monkeypatch) -> None:
    _configure_google(monkeypatch)
    monkeypatch.setattr(
        oauth_service,
        "fetch_google_profile",
        lambda code: {"sub": "google-user-2", "email": "returning@example.com", "nom": "Returning User"},
    )

    first = _callback(client, _begin_login(client))
    assert first.status_code == 302
    user = db_session.query(User).filter_by(email="returning@example.com").one()
    first_fragment = parse_qs(urlparse(first.headers["location"]).fragment)
    setup = client.post(
        "/api/auth/setup-password",
        json={"mot_de_passe": "returning-password-123"},
        headers=auth_headers(first_fragment["access_token"][0]),
    )
    assert setup.status_code == 200

    second = _callback(client, _begin_login(client))
    assert second.status_code == 302
    fragment = parse_qs(urlparse(second.headers["location"]).fragment)
    assert fragment["requires_password_setup"] == ["false"]
    assert db_session.query(User).filter_by(email="returning@example.com").count() == 1


def test_google_oauth_links_existing_email_account(client: TestClient, db_session, monkeypatch) -> None:
    from tests.conftest import create_user

    _configure_google(monkeypatch)
    existing = create_user(db_session, "Existing User", "existing@example.com")
    monkeypatch.setattr(
        oauth_service,
        "fetch_google_profile",
        lambda code: {"sub": "google-existing", "email": "EXISTING@example.com", "nom": "Google Name"},
    )

    callback = _callback(client, _begin_login(client))
    fragment = parse_qs(urlparse(callback.headers["location"]).fragment)
    assert fragment["requires_password_setup"] == ["false"]
    db_session.refresh(existing)
    assert existing.google_sub == "google-existing"
    assert db_session.query(User).filter_by(email="existing@example.com").count() == 1


def test_existing_users_table_gets_oauth_columns_and_index() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(320))"))
        connection.execute(text("INSERT INTO users (id, email) VALUES (1, 'existing@example.com')"))

    _ensure_user_auth_columns(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    indexes = {index["name"] for index in inspect(engine).get_indexes("users")}
    with engine.connect() as connection:
        assert connection.execute(text("SELECT password_set FROM users WHERE id = 1")).scalar() == 1
    assert {"password_set", "email_verified", "google_sub"} <= columns
    assert "ix_users_google_sub" in indexes
    engine.dispose()
