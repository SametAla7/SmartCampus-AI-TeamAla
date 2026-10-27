"""Schema Pydantic - QCM."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


class QCMSubmit(BaseModel):
    """Soumission d'un QCM : score obtenu (0-100)."""

    score: float = Field(..., ge=0.0, le=100.0)


class QCMRead(BaseModel):
    id: UUID
    candidature_id: UUID
    score: Optional[float] = None
    date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class QCMResultRead(BaseModel):
    score: Optional[float] = None
    date: Optional[datetime] = None
