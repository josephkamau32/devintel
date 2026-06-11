"""Organization schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.organization import OrganizationRole


# --- Core Schemas ---
class OrganizationBase(BaseModel):
    """Base Organization schema."""
    name: str = Field(..., description="The name of the organization")


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = Field(None, description="The new name of the organization")


class OrganizationRead(OrganizationBase):
    """Schema for reading an organization."""
    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# --- Member Schemas ---
class OrganizationMemberBase(BaseModel):
    """Base schema for an organization member."""
    role: OrganizationRole = Field(default=OrganizationRole.MEMBER)


class OrganizationMemberCreate(OrganizationMemberBase):
    """Schema for adding a member to an organization."""
    user_id: Optional[UUID] = Field(None, description="The user's ID to invite")
    username: Optional[str] = Field(None, description="The user's GitHub username to invite")
    email: Optional[str] = Field(None, description="The user's email to invite")


class OrganizationMemberUpdate(BaseModel):
    """Schema for updating an organization member's role."""
    role: OrganizationRole


class OrganizationMemberRead(OrganizationMemberBase):
    """Schema for reading an organization member."""
    user_id: UUID
    org_id: UUID
    joined_at: datetime

    # We will include basic user info if joined
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Composite Schemas ---
class OrganizationWithRole(OrganizationRead):
    """Organization schema with the current user's role."""
    my_role: OrganizationRole


class OrganizationDetailed(OrganizationRead):
    """Detailed organization schema with members."""
    members: list[OrganizationMemberRead] = []
