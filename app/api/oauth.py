"""Google OAuth routes."""

import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.core import security
from app.core.config import settings
from app.core.errors import APIError
from app.db.session import Session, get_db
from app.schemas.auth import TokenResponse
from app.schemas.user import UserRead
from app.services import oauth_service

router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])
_STATE_COOKIE = "google_oauth_state"
_COOKIE_PATH = f"{settings.API_PREFIX}/auth/oauth"


@router.get("/providers")
def providers() -> dict[str, bool | str]:
    configured = settings.google_oauth_configured
    return {
        "google": configured,
        "google_login_url": oauth_service.google_login_url() if configured else "",
    }


@router.get("/google/login")
def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(oauth_service.build_google_authorization_url(state), status_code=302)
    response.set_cookie(
        _STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=settings.APP_ENV != "development",
        path=_COOKIE_PATH,
    )
    return response


def _failure(error_code: str) -> RedirectResponse:
    response = RedirectResponse(
        f"{settings.FRONTEND_URL}/login?{urlencode({'error': error_code})}",
        status_code=302,
    )
    response.delete_cookie(_STATE_COOKIE, path=_COOKIE_PATH)
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if error:
        return _failure("oauth_denied")
    if not code or not state:
        return _failure("oauth_invalid_request")

    expected_state = request.cookies.get(_STATE_COOKIE, "")
    if not expected_state or not secrets.compare_digest(state, expected_state):
        return _failure("oauth_state_invalid")

    try:
        profile = oauth_service.fetch_google_profile(code)
        user = oauth_service.find_or_create_google_user(db, profile)
        if not user.est_actif:
            return _failure("user_inactive")
        tokens = TokenResponse(
            access_token=security.create_access_token(user.id, user.role.value),
            refresh_token=security.create_refresh_token(user.id, user.role.value),
            user=UserRead.model_validate(user),
            requires_password_setup=not user.password_set,
        )
    except APIError as exc:
        return _failure(exc.error_code.lower())

    fragment = urlencode(
        {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "requires_password_setup": str(tokens.requires_password_setup).lower(),
        }
    )
    response = RedirectResponse(f"{settings.FRONTEND_URL}/oauth/callback#{fragment}", status_code=302)
    response.delete_cookie(_STATE_COOKIE, path=_COOKIE_PATH)
    return response
