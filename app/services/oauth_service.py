"""Google OAuth helpers and account provisioning."""

import secrets
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core import security
from app.core.config import settings
from app.core.errors import APIError, conflict, service_unavailable
from app.db.session import Session
from app.models.user import User, UserRole

GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


def google_login_url() -> str:
    callback = urlsplit(settings.GOOGLE_REDIRECT_URI)
    path = f"{settings.API_PREFIX.rstrip('/')}/auth/oauth/google/login"
    return urlunsplit((callback.scheme, callback.netloc, path, "", ""))


def build_google_authorization_url(state: str) -> str:
    if not settings.google_oauth_configured:
        raise service_unavailable("OAUTH_NOT_CONFIGURED", "La connexion Google n'est pas configuree.")
    query = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{query}"


def fetch_google_profile(code: str) -> dict[str, str]:
    if not settings.google_oauth_configured:
        raise service_unavailable("OAUTH_NOT_CONFIGURED", "La connexion Google n'est pas configuree.")

    try:
        token_response = httpx.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise ValueError("Missing access token")

        profile_response = httpx.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        profile_response.raise_for_status()
        profile = profile_response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise APIError(502, "OAUTH_PROVIDER_UNREACHABLE", "Impossible de verifier le compte Google.") from exc

    email = str(profile.get("email", "")).strip().lower()
    subject = str(profile.get("sub", "")).strip()
    if not email or not subject or profile.get("email_verified") is not True:
        raise APIError(401, "OAUTH_EMAIL_NOT_VERIFIED", "Le compte Google doit avoir une adresse email verifiee.")

    name = str(profile.get("name", "")).strip()
    if not name:
        name = str(profile.get("given_name", "")).strip() or email.split("@", 1)[0]
    return {"sub": subject, "email": email, "nom": name[:150]}


def find_or_create_google_user(db: Session, profile: dict[str, str]) -> User:
    email = profile["email"].strip().lower()
    subject = profile["sub"]

    user = db.query(User).filter(User.google_sub == subject).first()
    if user is None:
        user = db.query(User).filter(func.lower(User.email) == email).first()

    if user is not None:
        if user.google_sub and user.google_sub != subject:
            raise conflict("OAUTH_ACCOUNT_CONFLICT", "Cette adresse email est deja associee a un autre compte Google.")
        changed = False
        if not user.google_sub:
            user.google_sub = subject
            changed = True
        if not user.email_verified:
            user.email_verified = True
            changed = True
        if changed:
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                raise conflict("OAUTH_ACCOUNT_CONFLICT", "Ce compte Google est deja associe a un autre utilisateur.")
            db.refresh(user)
        return user

    user = User(
        nom=profile["nom"],
        email=email,
        mot_de_passe=security.hash_password(secrets.token_urlsafe(48)),
        password_set=False,
        email_verified=True,
        google_sub=subject,
        role=UserRole.CANDIDAT,
        est_actif=True,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        existing = db.query(User).filter(
            (User.google_sub == subject) | (func.lower(User.email) == email)
        ).first()
        if existing is not None and (not existing.google_sub or existing.google_sub == subject):
            if not existing.google_sub:
                existing.google_sub = subject
                db.commit()
                db.refresh(existing)
            return existing
        raise conflict("OAUTH_ACCOUNT_CONFLICT", "Impossible d'associer ce compte Google a un utilisateur.")
