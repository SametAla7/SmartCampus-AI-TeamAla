"""Schema Pydantic."""

from app.schemas.auth import LoginRequest, MeResponse, RefreshRequest, TokenResponse
from app.schemas.candidature import (
    CandidatureCreate,
    CandidatureDecision,
    CandidatureListResponse,
    CandidatureRead,
    CandidatureStatutEnum,
    DecisionCandidatureEnum,
    DecisionCandidatureRead,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationRead,
    MessageCreate,
    MessageRead,
)
from app.schemas.dashboard import DashboardExportFormat, DashboardStats
from app.schemas.document import DocumentRead
from app.schemas.entretien import (
    DemandeComplementCreate,
    DemandeComplementRead,
    DemandeComplementStatutEnum,
    EntretienApproval,
    EntretienCreate,
    EntretienRead,
)
from app.schemas.parcours import ParcoursListResponse, ParcoursRead, ParcoursEtablissementEnum
from app.schemas.qcm import QCMRead, QCMResultRead, QCMSubmit
from app.schemas.user import UserCreate, UserListResponse, UserRead, UserRoleEnum, UserStatusUpdate, UserUpdate

__all__ = [
    "LoginRequest",
    "MeResponse",
    "RefreshRequest",
    "TokenResponse",
    "CandidatureCreate",
    "CandidatureDecision",
    "CandidatureListResponse",
    "CandidatureRead",
    "CandidatureStatutEnum",
    "DecisionCandidatureEnum",
    "DecisionCandidatureRead",
    "ConversationCreate",
    "ConversationDetailResponse",
    "ConversationRead",
    "MessageCreate",
    "MessageRead",
    "DashboardExportFormat",
    "DashboardStats",
    "DocumentRead",
    "DemandeComplementCreate",
    "DemandeComplementRead",
    "DemandeComplementStatutEnum",
    "EntretienApproval",
    "EntretienCreate",
    "EntretienRead",
    "ParcoursListResponse",
    "ParcoursRead",
    "ParcoursEtablissementEnum",
    "QCMRead",
    "QCMResultRead",
    "QCMSubmit",
    "UserCreate",
    "UserListResponse",
    "UserRead",
    "UserRoleEnum",
    "UserStatusUpdate",
    "UserUpdate",
]
