"""Service - Documents (metadonnees + stockage binaire)."""

import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import bad_request, forbidden, not_found
from app.db.session import Session
from app.models.candidature import Candidature
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.candidature_service import can_access_candidature


def add_document(db: Session, candidature_id: UUID, user: User, file: UploadFile) -> Document:
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if candidature is None:
        raise not_found("CANDIDATURE_NOT_FOUND", "Candidature introuvable.")
    if not can_access_candidature(db, user, candidature):
        raise forbidden("FORBIDDEN_DOCUMENT_ACCESS", "Acces refuse aux documents de cette candidature.")

    content = file.file.read() if file.file is not None else b""
    size = len(content)
    if size > settings.DOCUMENT_MAX_SIZE_MB * 1024 * 1024:
        raise bad_request("DOCUMENT_TOO_LARGE", f"Le fichier depasse la taille maximale de {settings.DOCUMENT_MAX_SIZE_MB} Mo.")
    if size == 0:
        raise bad_request("EMPTY_FILE", "Le fichier est vide.")
    filename = file.filename or "document"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in settings.DOCUMENT_ALLOWED_EXTENSIONS:
        raise bad_request("INVALID_FILE_TYPE", f"Type de fichier non autorise : {extension}.")

    storage_key = str(uuid.uuid4())
    storage_dir = Path(settings.DOCUMENT_STORAGE_PATH)
    storage_dir.mkdir(parents=True, exist_ok=True)
    destination = storage_dir / storage_key
    destination.write_bytes(content)

    document = Document(
        candidature_id=candidature_id,
        nom=filename,
        type=file.content_type or "application/octet-stream",
        taille_octets=size,
        storage_key=storage_key,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def list_documents(db: Session, candidature_id: UUID, user) -> list[DocumentRead]:
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if candidature is None:
        raise not_found("CANDIDATURE_NOT_FOUND", "Candidature introuvable.")
    if not can_access_candidature(db, user, candidature):
        raise forbidden("FORBIDDEN_DOCUMENT_ACCESS", "Acces refuse aux documents de cette candidature.")
    documents = db.query(Document).filter(Document.candidature_id == candidature_id).all()
    return [DocumentRead.model_validate(d) for d in documents]


def get_document(db: Session, document_id: UUID, user) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise not_found("DOCUMENT_NOT_FOUND", "Document introuvable.")
    candidature = db.query(Candidature).filter(Candidature.id == document.candidature_id).first()
    if candidature is None:
        raise not_found("CANDIDATURE_NOT_FOUND", "Candidature introuvable.")
    if not can_access_candidature(db, user, candidature):
        raise forbidden("FORBIDDEN_DOCUMENT_ACCESS", "Acces refuse aux documents de cette candidature.")
    return document


def get_document_file_path(document: Document) -> Path:
    storage_dir = Path(settings.DOCUMENT_STORAGE_PATH)
    return storage_dir / document.storage_key
