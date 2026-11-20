"""Service - Gestion des comptes utilisateurs (administrateur)."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core import security
from app.core.errors import conflict, not_found
from app.db.session import Session
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserStatusUpdate


def create_user(db: Session, data: UserCreate, email_verified: bool = True) -> UserRead:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing is not None:
        raise conflict("USER_EMAIL_ALREADY_EXISTS", "Un utilisateur existe deja avec cet email.")
    user = User(
        nom=data.nom,
        email=data.email,
        mot_de_passe=security.hash_password(data.mot_de_passe),
        email_verified=email_verified,
        role=data.role,
        est_actif=True,
        email_verified=email_verified,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise conflict("USER_EMAIL_ALREADY_EXISTS", "Un utilisateur existe deja avec cet email.")
    except Exception:
        db.rollback()
        raise
    return UserRead.model_validate(user)


def get_user_by_id(db: Session, user_id: UUID) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise not_found("USER_NOT_FOUND", "Utilisateur introuvable.")
    return user


def list_users(db: Session, page: int = 1, limit: int = 20) -> tuple[list[UserRead], int]:
    offset = (page - 1) * limit
    users = db.query(User).order_by(User.date_creation.desc()).offset(offset).limit(limit).all()
    total = db.query(User).count()
    return [UserRead.model_validate(u) for u in users], total


def update_user(db: Session, user_id: UUID, data: UserUpdate) -> User:
    user = get_user_by_id(db, user_id)
    if data.nom is not None:
        user.nom = data.nom
    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email).filter(User.id != user_id).first()
        if existing is not None:
            raise conflict("USER_EMAIL_ALREADY_EXISTS", "Un utilisateur existe deja avec cet email.")
        user.email = data.email
    if data.role is not None:
        user.role = UserRole(data.role.value)
    db.commit()
    db.refresh(user)
    return user


def set_user_status(db: Session, user_id: UUID, data: UserStatusUpdate) -> User:
    user = get_user_by_id(db, user_id)
    user.est_actif = data.est_actif
    db.commit()
    db.refresh(user)
    return user
