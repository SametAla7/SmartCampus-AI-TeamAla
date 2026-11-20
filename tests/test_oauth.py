"""Tests - OAuth 2.0 (connexion Google)."""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.core.config import settings
from app.core.errors import APIError
from app.models.user import User, UserRole
from app.services import oauth_service
from tests.conftest import create_user

CALLBACK = "/api/auth/oauth/google/callback"


@pytest.fixture()
def google_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-client-secret")


def _start_login(client: TestClient) -> str:
    """Appelle /google/login et retourne le parametre `state` envoye a Google."""
    response = client.get("/api/auth/oauth/google/login", follow_redirects=False)
    assert response.status_code == 302
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


def _fragment(location: str) -> dict:
    return {k: v[0] for k, v in parse_qs(urlparse(location).fragment).items()}


def _error_of(location: str) -> str:
    return parse_qs(urlparse(location).query)["error"][0]


def test_providers_reports_google_status(client: TestClient, google_configured) -> None:
    assert client.get("/api/auth/oauth/providers").json() == {"google": True}


def test_providers_false_when_not_configured(client: TestClient) -> None:
    assert client.get("/api/auth/oauth/providers").json() == {"google": False}


def test_login_returns_503_when_not_configured(client: TestClient) -> None:
    response = client.get("/api/auth/oauth/google/login", follow_redirects=False)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OAUTH_NOT_CONFIGURED"


def test_login_redirects_to_google_and_sets_nonce_cookie(client: TestClient, google_configured) -> None:
    response = client.get("/api/auth/oauth/google/login", follow_redirects=False)
    assert response.status_code == 302
    target = urlparse(response.headers["location"])
    query = parse_qs(target.query)
    assert target.netloc == "accounts.google.com"
    assert query["client_id"] == ["test-client-id"]
    assert query["redirect_uri"] == [settings.GOOGLE_REDIRECT_URI]
    assert query["response_type"] == ["code"]
    assert "email" in query["scope"][0]
    assert "oauth_nonce" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    payload = security.decode_oauth_state(query["state"][0])
    assert payload["nonce"]


def test_callback_creates_candidate_and_returns_working_tokens(
    client: TestClient, db_session, google_configured, monkeypatch
) -> None:
    monkeypatch.setattr(oauth_service, "fetch_google_profile", lambda code: {"email": "nouveau@gmail.com", "nom": "Nouvel Etudiant"})
    state = _start_login(client)

    response = client.get(CALLBACK, params={"code": "abc", "state": state}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"].startswith("http://localhost:4200/oauth/callback#")
    tokens = _fragment(response.headers["location"])

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "nouveau@gmail.com"
    assert me.json()["role"] == "CANDIDAT"
    assert client.post("/api/auth/refresh", json={"token": tokens["refresh_token"]}).status_code == 200


def test_callback_logs_into_existing_account_without_changing_role(
    client: TestClient, db_session, google_configured, monkeypatch
) -> None:
    existing = create_user(db_session, "Resp Academique", "resp@gmail.com", role=UserRole.RESPONSABLE_ACADEMIQUE)
    monkeypatch.setattr(oauth_service, "fetch_google_profile", lambda code: {"email": "resp@gmail.com", "nom": "Autre Nom"})
    state = _start_login(client)

    response = client.get(CALLBACK, params={"code": "abc", "state": state}, follow_redirects=False)
    tokens = _fragment(response.headers["location"])
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
    assert me["id"] == str(existing.id)
    assert me["role"] == "RESPONSABLE_ACADEMIQUE"
    assert db_session.query(User).filter(User.email == "resp@gmail.com").count() == 1


def test_callback_rejects_inactive_account(client: TestClient, db_session, google_configured, monkeypatch) -> None:
    create_user(db_session, "Inactif", "inactif@gmail.com", est_actif=False)
    monkeypatch.setattr(oauth_service, "fetch_google_profile", lambda code: {"email": "inactif@gmail.com", "nom": "Inactif"})
    state = _start_login(client)

    response = client.get(CALLBACK, params={"code": "abc", "state": state}, follow_redirects=False)
    assert response.headers["location"].startswith("http://localhost:4200/login?")
    assert _error_of(response.headers["location"]) == "user_inactive"


def test_callback_without_nonce_cookie_is_rejected(client: TestClient, google_configured, monkeypatch) -> None:
    called = []
    monkeypatch.setattr(oauth_service, "fetch_google_profile", lambda code: called.append(code))
    state = _start_login(client)
    client.cookies.clear()  # simule un state forge / injecte depuis un autre navigateur

    response = client.get(CALLBACK, params={"code": "abc", "state": state}, follow_redirects=False)
    assert _error_of(response.headers["location"]) == "oauth_state_invalid"
    assert called == []  # Google n'est meme pas contacte


def test_callback_rejects_forged_state(client: TestClient, google_configured) -> None:
    _start_login(client)
    response = client.get(CALLBACK, params={"code": "abc", "state": "forge"}, follow_redirects=False)
    assert _error_of(response.headers["location"]) == "oauth_state_invalid"


def test_callback_rejects_state_with_other_nonce(client: TestClient, google_configured) -> None:
    _start_login(client)  # cookie avec un nonce
    other_state = security.create_oauth_state("un-autre-nonce")
    response = client.get(CALLBACK, params={"code": "abc", "state": other_state}, follow_redirects=False)
    assert _error_of(response.headers["location"]) == "oauth_state_invalid"


def test_callback_handles_user_denial_and_missing_params(client: TestClient, google_configured) -> None:
    denied = client.get(CALLBACK, params={"error": "access_denied"}, follow_redirects=False)
    assert _error_of(denied.headers["location"]) == "oauth_denied"
    missing = client.get(CALLBACK, follow_redirects=False)
    assert _error_of(missing.headers["location"]) == "oauth_invalid_request"


def test_callback_never_puts_tokens_in_query_string(client: TestClient, google_configured, monkeypatch) -> None:
    monkeypatch.setattr(oauth_service, "fetch_google_profile", lambda code: {"email": "a.b@gmail.com", "nom": "A B"})
    state = _start_login(client)
    response = client.get(CALLBACK, params={"code": "abc", "state": state}, follow_redirects=False)
    assert urlparse(response.headers["location"]).query == ""


# --- fetch_google_profile : echange du code et verification de l'email ---------------------------


def _mock_google(monkeypatch, token_status=200, userinfo=None, userinfo_status=200) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(token_status, json={"access_token": "g-token"} if token_status == 200 else {"error": "bad"})
        return httpx.Response(userinfo_status, json=userinfo or {})

    real_client = httpx.Client
    monkeypatch.setattr(oauth_service.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))


def test_fetch_profile_success_normalizes_email(google_configured, monkeypatch) -> None:
    _mock_google(monkeypatch, userinfo={"email": "  Jean.Dupont@Gmail.com ", "email_verified": True, "name": "Jean Dupont"})
    assert oauth_service.fetch_google_profile("code") == {"email": "jean.dupont@gmail.com", "nom": "Jean Dupont"}


def test_fetch_profile_rejects_unverified_email(google_configured, monkeypatch) -> None:
    _mock_google(monkeypatch, userinfo={"email": "x@gmail.com", "email_verified": False, "name": "X Y"})
    with pytest.raises(APIError) as exc:
        oauth_service.fetch_google_profile("code")
    assert exc.value.error_code == "OAUTH_EMAIL_NOT_VERIFIED"


def test_fetch_profile_rejects_failed_code_exchange(google_configured, monkeypatch) -> None:
    _mock_google(monkeypatch, token_status=400)
    with pytest.raises(APIError) as exc:
        oauth_service.fetch_google_profile("mauvais-code")
    assert exc.value.error_code == "OAUTH_CODE_EXCHANGE_FAILED"


def test_fetch_profile_maps_network_errors_to_502(google_configured, monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    real_client = httpx.Client
    monkeypatch.setattr(oauth_service.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(APIError) as exc:
        oauth_service.fetch_google_profile("code")
    assert exc.value.status_code == 502
