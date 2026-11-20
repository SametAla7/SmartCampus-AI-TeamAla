"""Securite : hachage des mots de passe (Argon2) et JWT (access / refresh)."""

import datetime
import hashlib
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


def _password_fingerprint(hashed_password: str) -> str:
    """Empreinte courte du hash courant : un token de reinitialisation devient
    invalide des que le mot de passe change (usage unique, sans colonne en base)."""
    return hashlib.sha256(hashed_password.encode("utf-8")).hexdigest()[:16]


def create_password_reset_token(user_id: uuid.UUID, hashed_password: str) -> str:
    now = _now()
    exp_time = now + datetime.timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "password_reset",
        "pwd": _password_fingerprint(hashed_password),
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_password_reset_token(token: str) -> dict:
    try:
        return decode_token(token, expected_type="password_reset")
    except APIError:
        raise unauthenticated("RESET_TOKEN_INVALID", "Lien de reinitialisation invalide ou expire.")


def reset_token_matches_password(payload: dict, hashed_password: str) -> bool:
    return payload.get("pwd") == _password_fingerprint(hashed_password)


def create_email_verification_token(user_id: uuid.UUID, email: str) -> str:
    now = _now()
    exp_time = now + datetime.timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "type": "email_verification",
        "email": email.lower(),
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_email_verification_token(token: str) -> dict:
    try:
        return decode_token(token, expected_type="email_verification")
    except APIError:
        raise unauthenticated("EMAIL_VERIFICATION_INVALID", "Lien de verification invalide ou expire.")


def create_oauth_state(nonce: str) -> str:
    now = _now()
    exp_time = now + datetime.timedelta(minutes=settings.OAUTH_STATE_EXPIRE_MINUTES)
    payload = {
        "sub": "oauth",
        "type": "oauth_state",
        "nonce": nonce,
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_oauth_state(state: str) -> dict:
    try:
        return decode_token(state, expected_type="oauth_state")
    except APIError:
        raise unauthenticated("OAUTH_STATE_INVALID", "Parametre state OAuth invalide ou expire.")
