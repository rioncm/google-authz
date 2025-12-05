from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EffectiveAuth(BaseModel):
    """Normalized authorization payload."""

    email: str
    home_department: Optional[str] = None
    is_department_manager: bool = False
    functions: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    groups: List[str] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceAuthResponse(BaseModel):
    """Wrapper returned by the hard-coded test endpoint."""

    requested_email: str
    effective_auth: EffectiveAuth
    raw_user: Dict[str, Any]
    raw_groups: Dict[str, Any]
