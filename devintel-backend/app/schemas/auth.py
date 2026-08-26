import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GitHubCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class OAuthExchangeRequest(BaseModel):
    code: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    github_username: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool = False


TokenResponse.model_rebuild()
