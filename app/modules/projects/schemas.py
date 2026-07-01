from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.common.pagination import PageInfo
from app.modules.memory_entries.models import MemoryType
from app.modules.projects.models import ProjectRole, ProjectStatus


class ProjectSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    key: str
    name: str
    description: str | None
    status: ProjectStatus
    owning_group_id: UUID
    effective_role: ProjectRole | None


class ProjectListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProjectSummaryResponse]
    page: PageInfo


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
