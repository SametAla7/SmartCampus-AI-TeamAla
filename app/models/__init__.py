"""Modeles SQLAlchemy de la plateforme."""

from app.models.candidature import Candidature, CandidatureStatut, DecisionCandidature, DecisionCandidatureDecision, QCM
from app.models.conversation import Conversation, Message
from app.models.demande_complement import DemandeComplement, DemandeComplementStatut
from app.models.document import Document
from app.models.entretien import Entretien
from app.models.parcours import Parcours, ParcoursEtablissement
from app.models.user import User, UserRole

__all__ = [
    "Candidature",
    "CandidatureStatut",
    "DecisionCandidature",
    "DecisionCandidatureDecision",
    "QCM",
    "Conversation",
    "Message",
    "Document",
    "Entretien",
    "Parcours",
    "ParcoursEtablissement",
    "User",
    "UserRole",
    "DemandeComplement",
    "DemandeComplementStatut",
]
