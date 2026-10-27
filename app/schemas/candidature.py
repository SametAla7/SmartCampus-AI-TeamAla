"""Schema Pydantic - Candidature."""

from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.parcours import ParcoursRead


class CandidatureStatutEnum(str, Enum):
    EN_ATTENTE = "EN_ATTENTE"
    VALIDEE = "VALIDEE"
    REJETEE = "REJETEE"
    REORIENTEE = "REORIENTEE"


class DecisionCandidatureEnum(str, Enum):
    ACCEPTER = "ACCEPTER"
    REJETER = "REJETER"
    REORIENTER = "REORIENTER"


class CandidatureCreate(BaseModel):
    parcours_id: UUID


class CandidatureDecision(BaseModel):
    decision: DecisionCandidatureEnum
    commentaire: Optional[str] = Field(default=None, max_length=2000)
    parcours_destination_id: Optional[UUID] = None


class CandidatureRead(BaseModel):
    id: UUID
    candidat_id: UUID
    parcours: ParcoursRead
    date_depot: datetime
    statut: CandidatureStatutEnum
    responsable_academique_id: Optional[UUID] = None
    decision: Optional["DecisionCandidatureRead"] = None

    model_config = {"from_attributes": True}


class DecisionCandidatureRead(BaseModel):
    id: UUID
    candidature_id: UUID
    decision: DecisionCandidatureEnum
    commentaire: Optional[str] = None
    decisionne_par_id: Optional[UUID] = None
    date_decision: datetime
    parcours_destination_id: Optional[UUID] = None


class CandidatureListResponse(BaseModel):
    items: list[CandidatureRead]
    total: int
    page: int
    limit: int
