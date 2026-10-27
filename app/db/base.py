"""Entete de session SQLAlchemy declaratif."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative partagee par tous les modeles SQLAlchemy."""

    pass
