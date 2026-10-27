"""Schema Pydantic - Parcours."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ParcoursEtablissementEnum(str, Enum):
    IIT = "IIT"
    ISB = "ISB"


class ParcoursRead(BaseModel):
    id: UUID
    nom: str = Field(..., max_length=150)
    description: str | None = None
    etablissement: ParcoursEtablissementEnum
    created_at: datetime

    model_config = {"from_attributes": True}


class ParcoursListResponse(BaseModel):
    items: list[ParcoursRead]
