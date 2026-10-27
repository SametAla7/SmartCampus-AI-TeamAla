"""Securite : hachage des mots de passe (Argon2) et JWT (access / refresh)."""

import datetime
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError as PasswordVerificationError
from jose import JWTError, jwt

from app.core.config import settings
from app.core.errors import APIError, unauthenticated

_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)

_TOKEN_LIFETIME_ACCESS = datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
_TOKEN_LIFETIME_REFRESH = datetime.timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)


def hash_password(plain_password: str) -> str:
    """Retourne le hash Argon2 d'un mot de passe."""
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifie un mot de passe contre son hash (jamais de texte brut stocke)."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except PasswordVerificationError:
        return False


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _token_payload(user_id: uuid.UUID, token_type: str) -> dict:
    now = _now()
    lifetime = _TOKEN_LIFETIME_ACCESS if token_type == "access" else _TOKEN_LIFETIME_REFRESH
    exp_time = now + lifetime
    return {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
    }


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    payload = _token_payload(user_id, "access")
    payload["role"] = role
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID, role: str) -> str:
    payload = _token_payload(user_id, "refresh")
    payload["role"] = role
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Decodage et validation d'un JWT (signature, expiration, type)."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise unauthenticated("TOKEN_INVALID", "Token invalide ou expire.")

    if payload.get("type") != expected_type:
        raise unauthenticated("TOKEN_INVALID", "Type de token invalide.")

    user_id = payload.get("sub")
    if not user_id:
        raise unauthenticated("TOKEN_INVALID", "Token invalide.")

    return payload
