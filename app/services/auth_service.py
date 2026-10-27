"""Service - Authentification (login, tokens)."""

import uuid

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
    return user


def login(db: Session, login: LoginRequest) -> TokenResponse:
    user = authenticate(db, login)
    return TokenResponse(
        access_token=security.create_access_token(user.id, user.role.value),
        refresh_token=security.create_refresh_token(user.id, user.role.value),
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


def refresh(db: Session, refresh_token: str) -> TokenResponse:
    payload = security.decode_token(refresh_token, expected_type="refresh")
    user_id = uuid.UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.est_actif:
        raise unauthenticated("USER_INACTIVE", "Compte desactive.")
    return TokenResponse(
        access_token=security.create_access_token(user.id, user.role.value),
        refresh_token=security.create_refresh_token(user.id, user.role.value),
        token_type="bearer",
        user=UserRead.model_validate(user),
    )
