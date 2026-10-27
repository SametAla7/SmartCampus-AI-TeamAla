"""Schema Pydantic - Utilisateur."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRoleEnum(str, Enum):
    CANDIDAT = "CANDIDAT"
    RESPONSABLE_ACADEMIQUE = "RESPONSABLE_ACADEMIQUE"
    RESPONSABLE_ENTRETIEN = "RESPONSABLE_ENTRETIEN"
    DIRECTION = "DIRECTION"
    ADMINISTRATEUR = "ADMINISTRATEUR"


class UserBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=150)
    email: EmailStr = Field(..., max_length=320)


class UserCreate(UserBase):
    mot_de_passe: str = Field(..., min_length=8, max_length=128)
    role: UserRoleEnum = UserRoleEnum.CANDIDAT


class UserUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = Field(default=None, max_length=320)
    role: UserRoleEnum | None = None


class UserStatusUpdate(BaseModel):
    est_actif: bool


class UserRead(BaseModel):
    id: UUID
    nom: str
    email: str
    role: UserRoleEnum
    est_actif: bool
    date_creation: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    limit: int
