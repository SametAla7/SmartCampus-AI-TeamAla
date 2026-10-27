"""Schema Pydantic - Document."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: UUID
    candidature_id: UUID
    nom: str
    type: str
    taille_octets: int | None = None
    date_ajout: datetime

    model_config = {"from_attributes": True}
