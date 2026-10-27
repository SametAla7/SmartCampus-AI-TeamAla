"""Routes - Documents."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import not_found
from app.db.session import Session, get_db
from app.models.document import Document
from app.schemas.document import DocumentRead
from app.services.document_service import get_document, get_document_file_path

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{document_id}/download", summary="Telechargement controle d'un document")
def download_document_endpoint(document_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)) -> FileResponse:
    document = get_document(db, document_id, user)
    path = get_document_file_path(document)
    if not path.exists():
        from app.core.errors import not_found

        raise not_found("DOCUMENT_NOT_FOUND", "Document introuvable dans le stockage.")
    return FileResponse(path, media_type=document.type, filename=document.nom)
