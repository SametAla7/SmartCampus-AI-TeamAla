"""Routes - Authentification."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.db.session import Session, get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import login, refresh
from app.services.user_service import create_user

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse, summary="Authentification (email / mot de passe)")
def login_endpoint(login_request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return login(db, login_request)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Inscription candidat")
def register_endpoint(user_data: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    # Forcer le role candidat pour l'inscription publique
    user_data.role = UserRole.CANDIDAT
    return create_user(db, user_data)


@router.post("/refresh", response_model=TokenResponse, summary="Renouvellement du token d'acces")
def refresh_endpoint(refresh_request: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return refresh(db, refresh_request.token)


@router.get("/me", response_model=UserRead, summary="Utilisateur courant")
def me(user: User = Depends(get_current_user)) -> User:
    return user
