from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EffectiveAuth(BaseModel):
    """Normalized authorization payload."""

    email: str
    functions: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    groups: List[str] = Field(default_factory=list)
    custom_schemas: Dict[str, Dict[str, Dict[str, object]]] = Field(default_factory=dict)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceAuthResponse(BaseModel):
    """Wrapper returned by the hard-coded test endpoint."""

    requested_email: str
    effective_auth: EffectiveAuth
    raw_user: Dict[str, Any]
    raw_groups: Dict[str, Any]
