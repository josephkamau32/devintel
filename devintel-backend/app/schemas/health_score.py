from typing import Optional

from pydantic import BaseModel


class AutoFixRequest(BaseModel):
    issue_description: str


class AutoFixResponse(BaseModel):
    status: str
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    branch_name: Optional[str] = None
    message: Optional[str] = None
