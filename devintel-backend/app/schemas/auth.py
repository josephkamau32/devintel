from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
import re


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


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: Optional[str]
    full_name: Optional[str]
    github_username: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool


TokenResponse.model_rebuild()
