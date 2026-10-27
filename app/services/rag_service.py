"""Service - Administration RAG (reindexation des fichiers du corpus)."""

from pathlib import Path

from app.core.config import settings
from app.core.errors import service_unavailable
from app.db.session import Session


def is_rag_configured() -> bool:
    return bool(settings.RAG_CORPUS_DIR and settings.RAG_VECTOR_STORE and settings.RAG_EMBEDDING_PROVIDER)


def get_rag_status() -> dict:
    return {
        "configured": is_rag_configured(),
        "corpus_dir": settings.RAG_CORPUS_DIR,
        "vector_store": settings.RAG_VECTOR_STORE,
        "embedding_provider": settings.RAG_EMBEDDING_PROVIDER,
    }


def reindex() -> dict:
    """Declenche la reindexation du corpus documentaire.

    L'integration effective depend du fournisseur d'embeddings et du stock de
    vecteurs configure. Tant que ces elements ne sont pas disponibles, une
    erreur explicite est renvoyee (jamais de faux succes).
    """
    if not is_rag_configured():
        raise service_unavailable("RAG_NOT_CONFIGURED", "Le systeme RAG n'est pas configure (corpus, stock de vecteurs ou fournisseur d'embeddings manquant).")

    corpus_dir = Path(settings.RAG_CORPUS_DIR)
    if not corpus_dir.exists():
        raise service_unavailable("RAG_CORPUS_NOT_FOUND", "Le repertoire du corpus documentaire est introuvable.")

    # TODO : integration avec le vector store configure (embeddings + index).
    raise service_unavailable("RAG_EMBEDDING_NOT_IMPLEMENTED", "L'integration des embeddings du corpus n'est pas encore disponible.")
