from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.common.pagination import PageInfo
from app.modules.memory_entries.models import MemoryType


class ProjectTimelineEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    event_type: str
    memory_entry_id: UUID
    type: MemoryType
    title: str


class ProjectTimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    events: list[ProjectTimelineEventResponse]
    page: PageInfo
