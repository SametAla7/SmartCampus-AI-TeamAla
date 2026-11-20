"""Schema Pydantic - Authentification."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    mot_de_passe: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead
    requires_password_setup: bool = False


class SetupPasswordRequest(BaseModel):
    mot_de_passe: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
    token: str = Field(..., min_length=1)


class MeResponse(BaseModel):
    user: UserRead


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., max_length=320)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    nouveau_mot_de_passe: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., max_length=320)


class MessageResponse(BaseModel):
    message: str
