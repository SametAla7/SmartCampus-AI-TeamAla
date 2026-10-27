"""Schema Pydantic - Tableau de bord."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DashboardParcoursItem(BaseModel):
    parcours_id: Optional[str]
    nom: Optional[str]
    etablissement: Optional[str]
    total: int


class DashboardEvolutionItem(BaseModel):
    mois: str
    total: int


class DashboardStats(BaseModel):
    total_candidatures: int
    candidatures_par_statut: dict[str, int]
    candidatures_par_parcours: list[DashboardParcoursItem]
    nombre_entretiens: int
    evolution: list[DashboardEvolutionItem]


class DashboardExportFormat(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"
