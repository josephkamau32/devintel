from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: Optional[str]
    full_name: Optional[str]
    github_username: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
