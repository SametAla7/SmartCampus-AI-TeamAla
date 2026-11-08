"""Fournisseur de session SQLAlchemy."""

import os
import sys
from typing import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


def _preferred_postgres_driver() -> str:
    """Prefer psycopg (v3) for better unicode/hosted-DB handling; fallback to psycopg2."""
    try:
        import psycopg  # noqa: F401
        return "psycopg"
    except Exception:
        return "psycopg2"


def _normalize_database_url(url: str) -> str:
    """Normalize Prisma/Heroku-style postgres:// URLs for SQLAlchemy."""
    if not url:
        return url
    driver = _preferred_postgres_driver()
    # Allow explicit override to keep psycopg2 if needed
    if os.getenv("DB_FORCE_PSYCOPG2", "").lower() in {"1", "true", "yes"}:
        driver = "psycopg2"
    if url.startswith("postgres://"):
        return f"postgresql+{driver}://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        return f"postgresql+{driver}://" + url[len("postgresql://"):]
    # Upgrade explicit psycopg2 to psycopg v3 when available (better encoding/hosted DB support)
    if driver == "psycopg" and url.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + url[len("postgresql+psycopg2://"):]
    return url


database_url = _normalize_database_url(settings.effective_database_url)
is_postgres = database_url.startswith("postgresql")
is_sqlite = database_url.startswith("sqlite")


def _allow_non_remote_db() -> bool:
    return (
        os.getenv("SMARTCAMPUS_ALLOW_NON_REMOTE_DB", "").lower() in {"1", "true", "yes"}
        or (settings.APP_ENV or "").lower() in {"test", "testing"}
        or "pytest" in (sys.argv[0] or "").lower()
    )


def _url_parts(url: str) -> dict:
    """Return non-sensitive URL parts for diagnostics."""
    raw = url or ""
    scheme = raw.split("://", 1)[0] if "://" in raw else "unknown"
    parseable = raw
    if raw.startswith("postgresql+psycopg://"):
        parseable = "postgresql://" + raw[len("postgresql+psycopg://") :]
    elif raw.startswith("postgresql+psycopg2://"):
        parseable = "postgresql://" + raw[len("postgresql+psycopg2://") :]
    try:
        p = urlparse(parseable)
        host = p.hostname or ""
        dbname = (p.path or "").lstrip("/")
    except Exception:
        host, dbname = "", ""
    db_type = "sqlite" if scheme.startswith("sqlite") else ("postgresql" if "postgresql" in scheme else scheme)
    return {"type": db_type, "host": host or ("(local file)" if db_type == "sqlite" else "(unknown)"), "database": dbname}


def _is_local_or_unsafe_target(url: str) -> bool:
    if not url:
        return True
    if url.startswith("sqlite"):
        return True
    parts = _url_parts(url)
    host = (parts.get("host") or "").lower()
    return host in {"localhost", "127.0.0.1", ""}


# Safety: prevent silent fallback to local/SQLite in normal operation.
if _is_local_or_unsafe_target(database_url) and not _allow_non_remote_db():
    parts = _url_parts(database_url)
    raise RuntimeError(
        "Configuration base de donnees refusee: la cible resolue est locale/SQLite. "
        f"type={parts['type']} host={parts['host']} database={parts['database']}. "
        "Definissez DATABASE_URL (Prisma PostgreSQL heberge) dans le .env du projet "
        "(chemin resolu automatiquement) ou via variable d'environnement. "
        "Pour les tests uniquement, utilisez SMARTCAMPUS_ALLOW_NON_REMOTE_DB=1."
    )

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.DATABASE_ECHO,
}

if is_sqlite:
    connect_args = {"check_same_thread": False}
elif is_postgres:
    # Hosted Postgres (e.g., Prisma Postgres) typically requires SSL via URL params.
    # Keep pool settings conservative for serverless/pooled environments.
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        }
    )
    # Local Windows PostgreSQL setups may need specific encoding; only set if requested.
    if os.getenv("PG_FORCE_CLIENT_ENCODING"):
        connect_args = {"options": f"-c client_encoding={os.getenv('PG_FORCE_CLIENT_ENCODING')}"}

engine = create_engine(database_url, connect_args=connect_args, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)


def db_diagnostics() -> dict:
    """Safe diagnostics (no credentials/URL)."""
    parts = _url_parts(database_url)
    status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status = "connected"
    except Exception as e:
        status = f"error:{type(e).__name__}"
    return {**parts, "status": status}


def get_db() -> Generator[Session, None, None]:
    """Dependency FastAPI : fournit une session SQLAlchemy par requete."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
