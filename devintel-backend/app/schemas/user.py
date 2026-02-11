"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""

    id: UUID
    github_id: str
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
