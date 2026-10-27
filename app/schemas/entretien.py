"""Schema Pydantic - Entretien, DemandeComplement et QCM."""

from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class DemandeComplementStatutEnum(str, Enum):
    EN_ATTENTE = "EN_ATTENTE"
    TRAITEE = "TRAITEE"


class DemandeComplementCreate(BaseModel):
    contenu: str = Field(..., min_length=1, max_length=3000)
    informations_attendues: Optional[str] = Field(default=None, max_length=2000)
    type_document: Optional[str] = Field(default=None, max_length=100)


class DemandeComplementRead(BaseModel):
    id: UUID
    candidature_id: UUID
    contenu: str
    informations_attendues: Optional[str] = None
    type_document: Optional[str] = None
    statut: DemandeComplementStatutEnum
    date_demande: datetime
    demande_par_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


class EntretienCreate(BaseModel):
    date: datetime


class EntretienApproval(BaseModel):
    approuve: bool


class EntretienRead(BaseModel):
    id: UUID
    candidature_id: UUID
    date: datetime
    approuve: bool

    model_config = {"from_attributes": True}
