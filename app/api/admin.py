"""Routes - Administration (gestion des comptes, reindexation RAG)."""

from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.models.user import User, UserRole
from app.services.rag_service import get_rag_status, reindex

router = APIRouter(prefix="/admin", tags=["Administration"], dependencies=[Depends(require_role(UserRole.ADMINISTRATEUR))])


@router.post("/rag/reindex", summary="Declenchement de la reindexation des fichiers RAG")
def rag_reindex_endpoint() -> dict:
    return reindex()


@router.get("/rag/status", summary="Statut de configuration du systeme RAG")
def rag_status_endpoint() -> dict:
    return get_rag_status()
