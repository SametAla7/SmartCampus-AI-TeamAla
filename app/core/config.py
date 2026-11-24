"""Configuration de l'application SmartCampus AI.

Toutes les valeurs sont surchargeables via variables d'environnement
(ou fichier .env) - aucune valeur sensible n'est codée en dur en dur.
"""

from typing import List, Optional

from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to project root (parent of app/) so it works regardless of CWD.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    # Base de donnees
    # Pour Prisma Postgres: coller la chaine fournie dans .env (DATABASE_URL=...)
    # Formats acceptes: postgresql://..., postgres://..., postgresql+psycopg2://...
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/smartcampus"
    # URL directe optionnelle (recommandee pour migrations/DDL si Prisma fournit une URL non-poolee)
    DATABASE_URL_DIRECT: Optional[str] = None

    @staticmethod
    def _project_env_db_values() -> tuple[str, str]:
        """Read DB URL values from the project .env file (source of truth for DB config)."""
        try:
            values = dotenv_values(_ENV_FILE, encoding="utf-8-sig") if _ENV_FILE.exists() else {}
        except Exception:
            values = {}
        def pick(*keys: str) -> str:
            for k in keys:
                v = values.get(k)
                if v is None:
                    # case-insensitive fallback
                    for vk, vv in values.items():
                        if str(vk).upper() == k.upper() and vv is not None:
                            v = vv
                            break
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return ""
        return pick("DATABASE_URL"), pick("DATABASE_URL_DIRECT")

    @staticmethod
    def _is_remote_postgres_url(url: str) -> bool:
        u = (url or "").strip().lower()
        if not (u.startswith("postgres://") or u.startswith("postgresql://")):
            return False
        if "localhost" in u or "127.0.0.1" in u:
            return False
        return True

    @staticmethod
    def _is_local_or_sqlite_url(url: str) -> bool:
        u = (url or "").strip().lower()
        if not u:
            return True
        if u.startswith("sqlite"):
            return True
        if "localhost" in u or "127.0.0.1" in u:
            return True
        return False

    @property
    def effective_database_url(self) -> str:
        """URL effective: privilegie la config DB du .env projet/Prisma, refuse les cibles locales/SQLite accidentelles."""
        env_url = (self.DATABASE_URL or "").strip()
        env_direct = (self.DATABASE_URL_DIRECT or "").strip()
        file_url, file_direct = self._project_env_db_values()

        local_default_markers = ("localhost", "127.0.0.1")
        remote_markers = ("prisma.io", "neon.tech", "supabase", "amazonaws.com", "azure.com", "render.com", "railway", "pooler", ".db.")

        def resolve(url: str, direct: str) -> str:
            url = (url or "").strip()
            direct = (direct or "").strip()
            if url and direct:
                url_l = url.lower()
                direct_l = direct.lower()
                if any(m in url_l for m in local_default_markers) and (self._is_remote_postgres_url(direct) or any(m in direct_l for m in remote_markers)):
                    return direct
            if url:
                return url
            if direct:
                return direct
            return ""

        resolved = resolve(env_url, env_direct)
        resolved_file = resolve(file_url, file_direct)

        # Si l'environnement/process (ex: variable PowerShell) impose une cible locale/SQLite,
        # mais que le .env projet definit une cible Postgres distante/Prisma, utiliser le .env projet.
        if self._is_local_or_sqlite_url(resolved) and self._is_remote_postgres_url(resolved_file):
            return resolved_file

        # Fallback: if project file has remote config and nothing resolved
        if not resolved and self._is_remote_postgres_url(resolved_file):
            return resolved_file

        if resolved:
            return resolved

        raise RuntimeError(
            "Aucune configuration de base de donnees trouvee. "
            f"Definissez DATABASE_URL (ou DATABASE_URL_DIRECT) dans {_ENV_FILE}."
        )
    DATABASE_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 1800
    # Controle la creation automatique des tables au demarrage (utile en dev; en prod preferer les migrations)
    CREATE_TABLES_ON_STARTUP: bool = True

    # Authentification JWT
    JWT_SECRET: str = "smartcampus-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Argon2 - hachage des mots de passe
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 1

    # Application
    APP_NAME: str = "SmartCampus AI"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:4200", "http://127.0.0.1:4200"]

    # Stockage des documents (métadonnées en base, binaire hors base)
    DOCUMENT_STORAGE_PATH: str = "/tmp/smartcampus_documents"
    DOCUMENT_MAX_SIZE_MB: int = 10
    DOCUMENT_ALLOWED_EXTENSIONS: List[str] = [
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "doc",
        "docx",
        "txt",
        "csv",
    ]

    # Chatbot / RAG - non operationnel tant que non configure
    CHATBOT_ENABLED: bool = False
    CHATBOT_PROVIDER: Optional[str] = None
    CHATBOT_API_KEY: Optional[str] = None
    COLAB_INFERENCE_URL: Optional[str] = None
    COLAB_INFERENCE_CHAT_ENDPOINT: str = "/chat"
    COLAB_INFERENCE_API_KEY: Optional[str] = None
    COLAB_INFERENCE_TIMEOUT_SECONDS: int = 180
    COLAB_INFERENCE_HISTORY_LIMIT: int = 20
    RAG_CORPUS_DIR: Optional[str] = None
    RAG_VECTOR_STORE: Optional[str] = None
    RAG_EMBEDDING_PROVIDER: Optional[str] = None

    # Responsable academique attribue par defaut aux nouvelles candidatures
    DEFAULT_RESPONSABLE_ACADEMIQUE_ID: Optional[str] = None

    FRONTEND_URL: str = "http://localhost:4200"

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_STARTTLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: str = "SmartCampus AI"
    SMTP_TIMEOUT_SECONDS: int = 10
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24

    @property
    def smtp_configured(self) -> bool:
        return bool((self.SMTP_HOST or "").strip() and (self.SMTP_FROM_EMAIL or "").strip())

    # OAuth 2.0 - Google
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/api/auth/oauth/google/callback"

    @property
    def google_oauth_configured(self) -> bool:
        return bool((self.GOOGLE_CLIENT_ID or "").strip() and (self.GOOGLE_CLIENT_SECRET or "").strip())


settings = Settings()
