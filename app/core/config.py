"""Configuration de l'application SmartCampus AI.

Toutes les valeurs sont surchargeables via variables d'environnement
(ou fichier .env) - aucune valeur sensible n'est codée en dur en dur.
"""

from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de données
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/smartcampus"
    DATABASE_ECHO: bool = False

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
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

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
    RAG_CORPUS_DIR: Optional[str] = None
    RAG_VECTOR_STORE: Optional[str] = None
    RAG_EMBEDDING_PROVIDER: Optional[str] = None

    # Responsable academique attribue par defaut aux nouvelles candidatures
    DEFAULT_RESPONSABLE_ACADEMIQUE_ID: Optional[str] = None


settings = Settings()
