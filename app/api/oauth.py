"""Routes - OAuth 2.0 (connexion via Google).

Flux : le frontend envoie le navigateur vers GET /api/auth/oauth/google/login
-> Google -> GET /api/auth/oauth/google/callback -> redirection vers le frontend :
  succes : {FRONTEND_URL}/oauth/callback#access_token=...&refresh_token=...
  erreur : {FRONTEND_URL}/login?error=<code>
Les jetons sont places dans le fragment (#) pour ne pas apparaitre dans les logs serveur.

Protection CSRF : `state` est un JWT signe contenant un nonce, et le meme nonce est
depose dans un cookie HttpOnly ; le callback exige que les deux correspondent.
"""

import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.core import security
from app.core.config import settings
from app.core.errors import APIError
from app.db.session import Session, get_db
from app.services import oauth_service
from app.services.auth_service import build_token_response

router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])

_NONCE_COOKIE = "oauth_nonce"
_COOKIE_PATH = f"{settings.API_PREFIX}/auth/oauth"


@router.get("/providers", summary="Fournisseurs OAuth disponibles")
def providers() -> dict:
    return {"google": settings.google_oauth_configured}


@router.get("/google/login", summary="Demarre la connexion Google (redirige vers Google)")
def google_login() -> RedirectResponse:
    nonce = oauth_service.new_nonce()
    url = oauth_service.build_google_authorization_url(security.create_oauth_state(nonce))
    response = RedirectResponse(url, status_code=302)
    response.set_cookie(
        _NONCE_COOKIE,
        nonce,
        max_age=settings.OAUTH_STATE_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=settings.APP_ENV != "development",
        path=_COOKIE_PATH,
    )
    return response


def _failure(error_code: str) -> RedirectResponse:
    response = RedirectResponse(f"{settings.FRONTEND_URL}/login?{urlencode({'error': error_code})}", status_code=302)
    response.delete_cookie(_NONCE_COOKIE, path=_COOKIE_PATH)
    return response


@router.get("/google/callback", summary="Retour de Google (echange du code, emission des jetons)")
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if error:
        return _failure("oauth_denied")  # l'utilisateur a refuse / annule chez Google
    if not code or not state:
        return _failure("oauth_invalid_request")

    try:
        payload = security.decode_oauth_state(state)
    except APIError:
        return _failure("oauth_state_invalid")
    cookie_nonce = request.cookies.get(_NONCE_COOKIE) or ""
    if not cookie_nonce or not secrets.compare_digest(cookie_nonce.encode(), str(payload.get("nonce", "")).encode()):
        return _failure("oauth_state_invalid")

    try:
        profile = oauth_service.fetch_google_profile(code)
        user = oauth_service.find_or_create_oauth_user(db, profile["email"], profile["nom"])
        tokens = build_token_response(user)
    except APIError as exc:
        return _failure(exc.error_code.lower())

    fragment = urlencode(
        {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token, "token_type": "bearer"}
    )
    response = RedirectResponse(f"{settings.FRONTEND_URL}/oauth/callback#{fragment}", status_code=302)
    response.delete_cookie(_NONCE_COOKIE, path=_COOKIE_PATH)
    return response
