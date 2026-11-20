"""Point d'entree de l'application SmartCampus AI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api import admin, auth, candidatures, conversations, dashboard, documents, entretiens, oauth, parcours, users
from app.core.config import settings
from app.core.errors import APIError
from app.db.base import Base
from app.db.session import db_diagnostics, engine

logger = logging.getLogger("smartcampus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    diag = db_diagnostics()
    # Safe diagnostic only (no credentials/URL/password).
    logger.info(
        "DB startup: type=%s host=%s database=%s status=%s",
        diag.get("type"), diag.get("host"), diag.get("database"), diag.get("status"),
    )
    print(
        f"[SmartCampus DB] type={diag.get('type')} host={diag.get('host')} "
        f"database={diag.get('database')} status={diag.get('status')}",
        flush=True,
    )
    if str(diag.get("status", "")).startswith("error"):
        raise RuntimeError(
            "Echec de connexion a la base de donnees au demarrage "
            f"(type={diag.get('type')} host={diag.get('host')} database={diag.get('database')}). "
            "Verifiez DATABASE_URL/DATABASE_URL_DIRECT dans le .env du projet, reseau et SSL."
        )
    # Création des tables au démarrage si activée (dev). En production, préférer les migrations Alembic.
    try:
        if settings.CREATE_TABLES_ON_STARTUP:
            Base.metadata.create_all(bind=engine)
        if inspect(engine).has_table("users"):
            columns = {column["name"] for column in inspect(engine).get_columns("users")}
            if "email_verified" not in columns:
                # Existing accounts predate verification and remain usable; new public signups opt out.
                with engine.begin() as connection:
                    connection.execute(
                        text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT TRUE")
                    )
    except Exception as exc:
        raise RuntimeError(
            "Echec de l'initialisation du schema au demarrage. "
            "Verifiez les droits/schema (sans exposer d'identifiants)."
        ) from exc
    yield
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Plateforme intelligente d'orientation universitaire (IIT / ISB).",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(oauth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(parcours.router, prefix=settings.API_PREFIX)
app.include_router(conversations.router, prefix=settings.API_PREFIX)
app.include_router(candidatures.router, prefix=settings.API_PREFIX)
app.include_router(entretiens.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)


@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "error": {"code": exc.error_code}})


@app.get("/api/health", summary="Salud de l'application")
def health() -> dict:
    return {"status": "ok"}
