"""Routes - Authentification."""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core import security
from app.core.errors import conflict
from app.api.deps import get_current_user, get_user_for_password_setup
from app.db.session import Session, get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    SetupPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import login, prepare_email_verification, refresh, verify_email
from app.services.email_service import send_email_verification_email
from app.services.user_service import create_user

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse, summary="Authentification (email / mot de passe)")
def login_endpoint(login_request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return login(db, login_request)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Inscription candidat")
def register_endpoint(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> UserRead:
    # Forcer le role candidat pour l'inscription publique
    user_data.role = UserRole.CANDIDAT
    created = create_user(db, user_data, email_verified=False)
    token = security.create_email_verification_token(created.id, created.email)
    background_tasks.add_task(send_email_verification_email, created.nom, created.email, token)
    return created


@router.post("/verify-email", response_model=MessageResponse)
def verify_email_endpoint(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageResponse:
    verify_email(db, payload.token)
    return MessageResponse(message="Email verified. You can now sign in.")


@router.post("/resend-verification", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def resend_verification_endpoint(
    payload: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> MessageResponse:
    prepared = prepare_email_verification(db, payload.email)
    if prepared is not None:
        background_tasks.add_task(send_email_verification_email, *prepared)
    return MessageResponse(message="If this account needs verification, a new link has been sent.")


@router.post("/refresh", response_model=TokenResponse, summary="Renouvellement du token d'acces")
def refresh_endpoint(refresh_request: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return refresh(db, refresh_request.token)


@router.get("/me", response_model=UserRead, summary="Utilisateur courant")
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/setup-password", response_model=MessageResponse, summary="Configurer le mot de passe d'un compte Google")
def setup_password_endpoint(
    payload: SetupPasswordRequest,
    user: User = Depends(get_user_for_password_setup),
    db: Session = Depends(get_db),
) -> MessageResponse:
    if user.password_set:
        raise conflict("PASSWORD_ALREADY_SET", "Le mot de passe de ce compte est deja configure.")
    user.mot_de_passe = security.hash_password(payload.mot_de_passe)
    user.password_set = True
    db.commit()
    return MessageResponse(message="Profil configure. Vous pouvez maintenant acceder aux conversations.")
