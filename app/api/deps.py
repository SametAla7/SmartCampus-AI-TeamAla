"""Dependances FastAPI - authentification et autorisations."""

from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.errors import forbidden, unauthenticated
from app.db.session import Session as DBSession, get_db
from app.models.user import User, UserRole
from app.schemas.user import UserRead

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Bearer")


def _authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Retourne l'utilisateur authentifie via JWT Bearer token."""
    if credentials is None or not credentials.credentials or credentials.scheme.lower() != "bearer":
        raise unauthenticated("TOKEN_MISSING", "Token d'authentification requis.")
    payload = security.decode_token(credentials.credentials, expected_type="access")
    user_id = UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.est_actif.is_(True)).first()
    if user is None:
        raise unauthenticated("USER_NOT_FOUND", "Utilisateur introuvable ou desactive.")
    return user


def get_current_user(user: User = Depends(_authenticated_user)) -> User:
    if not user.password_set:
        raise unauthenticated("PASSWORD_SETUP_REQUIRED", "Veuillez terminer la configuration de votre profil.")
    return user


def get_user_for_password_setup(user: User = Depends(_authenticated_user)) -> User:
    return user


def require_role(*roles: UserRole):
    """Factory de dependance FastAPI : verifie que l'utilisateur a un role autorise."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise forbidden(
                "FORBIDDEN_ROLE",
                f"Acces reserve au role : {', '.join(r.value for r in roles)}.",
            )
        return user

    return checker
