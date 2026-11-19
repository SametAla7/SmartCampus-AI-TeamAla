"""Routes - Authentification."""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps import get_current_user
from app.core import security
from app.db.session import Session, get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    login,
    prepare_email_verification,
    refresh,
    request_password_reset,
    reset_password,
    verify_email,
)
from app.services.email_service import send_email_verification_email, send_password_reset_email
from app.services.user_service import create_user

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse, summary="Authentification (email / mot de passe)")
def login_endpoint(login_request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return login(db, login_request)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Inscription candidat")
def register_endpoint(
    user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> UserRead:
    # Forcer le role candidat pour l'inscription publique
    user_data.role = UserRole.CANDIDAT
    created = create_user(db, user_data, email_verified=False)
    token = security.create_email_verification_token(created.id, created.email)
    background_tasks.add_task(send_email_verification_email, created.nom, created.email, token)
    return created


@router.post("/verify-email", response_model=MessageResponse, summary="Confirmer une adresse email")
def verify_email_endpoint(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageResponse:
    verify_email(db, payload.token)
    return MessageResponse(message="Adresse email confirmée. Vous pouvez maintenant vous connecter.")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Renvoyer le lien de confirmation",
)
def resend_verification_endpoint(
    payload: ResendVerificationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> MessageResponse:
    prepared = prepare_email_verification(db, payload.email)
    if prepared is not None:
        nom, email, token = prepared
        background_tasks.add_task(send_email_verification_email, nom, email, token)
    return MessageResponse(message="Si ce compte doit être vérifié, un nouveau lien vient d’être envoyé.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Demande de reinitialisation du mot de passe (envoi d'un email)",
)
def forgot_password_endpoint(
    payload: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> MessageResponse:
    prepared = request_password_reset(db, payload.email)
    if prepared is not None:
        nom, email, token = prepared
        background_tasks.add_task(send_password_reset_email, nom, email, token)
    # Reponse identique que le compte existe ou non (pas d'enumeration de comptes).
    return MessageResponse(message="Si un compte correspond a cet email, un lien de reinitialisation vient d'etre envoye.")


@router.post("/reset-password", response_model=MessageResponse, summary="Definir un nouveau mot de passe via le lien recu")
def reset_password_endpoint(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    reset_password(db, payload.token, payload.nouveau_mot_de_passe)
    return MessageResponse(message="Mot de passe mis a jour. Vous pouvez maintenant vous connecter.")


@router.post("/refresh", response_model=TokenResponse, summary="Renouvellement du token d'acces")
def refresh_endpoint(refresh_request: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return refresh(db, refresh_request.token)


@router.get("/me", response_model=UserRead, summary="Utilisateur courant")
def me(user: User = Depends(get_current_user)) -> User:
    return user
