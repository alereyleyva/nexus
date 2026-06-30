from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.pagination import PageInfo
from app.modules.memory_entries.models import MemoryStatus, MemoryType, VisibilityScope


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    project_id: UUID | None = None
    types: list[MemoryType] = Field(default_factory=list)
    statuses: list[MemoryStatus] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)
    cursor: str | None = None
    include_evidence: bool = False


class SearchResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    type: MemoryType
    title: str
    body: str
    status: MemoryStatus
    visibility_scope: VisibilityScope
    project_id: UUID | None
    tags: list[str]
    score: float
    evidence_count: int
    needs_review_warning: bool


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[SearchResultResponse]
    page: PageInfo
