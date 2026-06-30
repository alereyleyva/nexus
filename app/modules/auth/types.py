from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.memory_entries.models import VisibilityScope


class ActorContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    org_id: UUID
    user_id: UUID
    session_id: UUID
    session_capabilities: set[str]
    session_max_visibility_scope: VisibilityScope | None
    client_type: Literal["web", "cli", "future_integration"]
    request_id: str
