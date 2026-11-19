"""Service - Authentification (login, tokens)."""

import uuid

from sqlalchemy import func

from app.core import security
from app.core.errors import unauthenticated
from app.db.session import Session
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead


def authenticate(db: Session, login: LoginRequest) -> User:
    """Authentifie un utilisateur par email / mot de passe."""
    user = db.query(User).filter(User.email == login.email).first()
    if user is None or not security.verify_password(login.mot_de_passe, user.mot_de_passe):
        raise unauthenticated("INVALID_CREDENTIALS", "Email ou mot de passe invalide.")
    if not user.est_actif:
        raise unauthenticated("USER_INACTIVE", "Ce compte est desactive.")
    if not user.email_verified:
        raise unauthenticated("EMAIL_NOT_VERIFIED", "Veuillez verifier votre adresse email avant de vous connecter.")
    return user


def login(db: Session, login: LoginRequest) -> TokenResponse:
    user = authenticate(db, login)
    return TokenResponse(
        access_token=security.create_access_token(user.id, user.role.value),
        refresh_token=security.create_refresh_token(user.id, user.role.value),
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


def build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=security.create_access_token(user.id, user.role.value),
        refresh_token=security.create_refresh_token(user.id, user.role.value),
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


def request_password_reset(db: Session, email: str) -> tuple[str, str, str] | None:
    """Prepare une reinitialisation : retourne (nom, email, token) ou None si le compte
    n'existe pas / est desactive. L'appelant ne doit JAMAIS reveler laquelle des deux
    situations s'est produite (pas d'enumeration de comptes)."""
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if user is None or not user.est_actif:
        return None
    token = security.create_password_reset_token(user.id, user.mot_de_passe)
    return user.nom, user.email, token


def reset_password(db: Session, token: str, new_password: str) -> None:
    payload = security.decode_password_reset_token(token)
    invalid = unauthenticated("RESET_TOKEN_INVALID", "Lien de reinitialisation invalide ou expire.")
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise invalid
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.est_actif:
        raise invalid
    if not security.reset_token_matches_password(payload, user.mot_de_passe):
        # Mot de passe deja change depuis l'emission du lien : lien a usage unique.
        raise invalid
    user.mot_de_passe = security.hash_password(new_password)
    db.commit()


def verify_email(db: Session, token: str) -> None:
    payload = security.decode_email_verification_token(token)
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise unauthenticated("EMAIL_VERIFICATION_INVALID", "Lien de verification invalide ou expire.")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.email.lower() != str(payload.get("email", "")).lower():
        raise unauthenticated("EMAIL_VERIFICATION_INVALID", "Lien de verification invalide ou expire.")
    if user.email_verified:
        return
    user.email_verified = True
    db.commit()


def prepare_email_verification(db: Session, email: str) -> tuple[str, str, str] | None:
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if user is None or not user.est_actif or user.email_verified:
        return None
    token = security.create_email_verification_token(user.id, user.email)
    return user.nom, user.email, token


def refresh(db: Session, refresh_token: str) -> TokenResponse:
    payload = security.decode_token(refresh_token, expected_type="refresh")
    user_id = uuid.UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.est_actif:
        raise unauthenticated("USER_INACTIVE", "Compte desactive.")
    if not user.email_verified:
        raise unauthenticated("EMAIL_NOT_VERIFIED", "Veuillez verifier votre adresse email avant de vous connecter.")
    return TokenResponse(
        access_token=security.create_access_token(user.id, user.role.value),
        refresh_token=security.create_refresh_token(user.id, user.role.value),
        token_type="bearer",
        user=UserRead.model_validate(user),
    )
