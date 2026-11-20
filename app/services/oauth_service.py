"""Service - OAuth 2.0 / OpenID Connect (Google), flux "authorization code".

Aucun changement de schema : un utilisateur cree via Google recoit un mot de passe
aleatoire (hache Argon2) que personne ne connait ; il se connecte uniquement via
Google, ou definit un mot de passe via "mot de passe oublie".
"""

import logging
import secrets
from urllib.parse import urlencode

import httpx
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core import security
from app.core.config import settings
from app.core.errors import api_error, service_unavailable, unauthenticated
from app.db.session import Session
from app.models.user import User, UserRole

logger = logging.getLogger("smartcampus.oauth")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
_HTTP_TIMEOUT = 10.0


def ensure_google_configured() -> None:
    if not settings.google_oauth_configured:
        raise service_unavailable(
            "OAUTH_NOT_CONFIGURED", "La connexion Google n'est pas configuree (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET)."
        )


def new_nonce() -> str:
    return secrets.token_urlsafe(32)


def build_google_authorization_url(state: str) -> str:
    ensure_google_configured()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def fetch_google_profile(code: str) -> dict:
    """Echange le code d'autorisation puis lit le profil. Retourne {email, nom}.

    Refuse tout compte Google dont l'email n'est pas verifie (sinon on pourrait
    prendre le controle d'un compte existant avec un email non verifie)."""
    ensure_google_configured()
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            token_response = client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if token_response.status_code != 200:
                logger.warning("Echange du code Google refuse (HTTP %s).", token_response.status_code)
                raise unauthenticated("OAUTH_CODE_EXCHANGE_FAILED", "Echec de l'authentification Google.")
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise unauthenticated("OAUTH_CODE_EXCHANGE_FAILED", "Echec de l'authentification Google.")
            info_response = client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
            if info_response.status_code != 200:
                raise unauthenticated("OAUTH_PROFILE_FAILED", "Impossible de lire le profil Google.")
            info = info_response.json()
    except httpx.HTTPError as exc:
        logger.error("Google injoignable : %s", type(exc).__name__)
        raise api_error(502, "OAUTH_PROVIDER_UNREACHABLE", "Le service Google est injoignable.")

    email = str(info.get("email") or "").strip().lower()
    verified = info.get("email_verified")
    if isinstance(verified, str):
        verified = verified.strip().lower() == "true"
    if not email or "@" not in email or verified is not True:
        raise unauthenticated("OAUTH_EMAIL_NOT_VERIFIED", "L'email du compte Google n'est pas verifie.")
    nom = str(info.get("name") or "").strip() or email.split("@")[0]
    if len(nom) < 2:
        nom = email.split("@")[0]
    return {"email": email, "nom": nom[:150]}


def find_or_create_oauth_user(db: Session, email: str, nom: str) -> User:
    """Retrouve le compte par email (insensible a la casse) ou cree un CANDIDAT."""

    def lookup() -> User | None:
        return db.query(User).filter(func.lower(User.email) == email.lower()).first()

    user = lookup()
    if user is None:
        user = User(
            nom=nom,
            email=email,
            mot_de_passe=security.hash_password(secrets.token_urlsafe(32)),
            role=UserRole.CANDIDAT,
            est_actif=True,
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError:
            # Creation concurrente du meme email : on reprend le compte existant.
            db.rollback()
            user = lookup()
            if user is None:
                raise
    if not user.est_actif:
        raise unauthenticated("USER_INACTIVE", "Ce compte est desactive.")
    if not user.email_verified:
        user.email_verified = True
        db.commit()
    return user
