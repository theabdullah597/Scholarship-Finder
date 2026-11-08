import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentProfileResponse(BaseModel):
    id: uuid.UUID
    full_name: str | None = None
    citizenship: str | None = None
    target_countries: list[str] = Field(default_factory=list)
    fields_of_interest: list[str] = Field(default_factory=list)
    target_degree_level: str | None = None
    timezone: str = "UTC"

    model_config = ConfigDict(from_attributes=True)


class StudentProfileUpdate(BaseModel):
    full_name: str | None = None
    citizenship: str | None = Field(default=None, max_length=2)
    target_countries: list[str] | None = None
    fields_of_interest: list[str] | None = None
    target_degree_level: str | None = None
    timezone: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_verified: bool
    created_at: datetime
    profile: StudentProfileResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    message: str
