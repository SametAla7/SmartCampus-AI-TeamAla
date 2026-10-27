"""Routes - Gestion des comptes utilisateurs (administrateur)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import require_role
from app.db.session import Session, get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserListResponse, UserRead, UserStatusUpdate, UserUpdate
from app.services.user_service import create_user, get_user_by_id, list_users, set_user_status, update_user

router = APIRouter(prefix="/users", tags=["Utilisateurs"], dependencies=[Depends(require_role(UserRole.ADMINISTRATEUR))])


@router.get("", response_model=UserListResponse, summary="Liste des utilisateurs (pagination)")
def list_users_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> UserListResponse:
    items, total = list_users(db, page=page, limit=limit)
    return UserListResponse(items=[UserRead.model_validate(i) for i in items], total=total, page=page, limit=limit)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Creation d'un compte utilisateur")
def create_user_endpoint(user_data: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    return create_user(db, user_data)


@router.get("/{user_id}", response_model=UserRead, summary="Consultation d'un utilisateur")
def get_user_endpoint(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    return get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserRead, summary="Modification d'un utilisateur")
def update_user_endpoint(user_id: UUID, user_data: UserUpdate, db: Session = Depends(get_db)) -> UserRead:
    return update_user(db, user_id, user_data)


@router.patch("/{user_id}/status", response_model=UserRead, summary="Activation / desactivation d'un compte")
def set_user_status_endpoint(user_id: UUID, status_data: UserStatusUpdate, db: Session = Depends(get_db)) -> UserRead:
    return set_user_status(db, user_id, status_data)
