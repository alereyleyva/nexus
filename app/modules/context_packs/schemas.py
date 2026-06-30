from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.memory_entries.models import MemoryStatus, MemoryType


class ContextPackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID | None = None
    task: str | None = None
    query: str | None = None
    max_items: int = Field(default=20, ge=1, le=50)
    include_types: list[MemoryType] = Field(default_factory=list)


class ContextPackItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    title: str
    body: str
    status: MemoryStatus
    evidence_count: int


class ContextPackWarningResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    message: str


class ContextPackItemsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decisions: list[ContextPackItemResponse] = Field(default_factory=list)
    problems: list[ContextPackItemResponse] = Field(default_factory=list)
    solutions: list[ContextPackItemResponse] = Field(default_factory=list)
    failed_attempts: list[ContextPackItemResponse] = Field(default_factory=list)
    risks: list[ContextPackItemResponse] = Field(default_factory=list)
    procedures: list[ContextPackItemResponse] = Field(default_factory=list)
    open_questions: list[ContextPackItemResponse] = Field(default_factory=list)
    tasks: list[ContextPackItemResponse] = Field(default_factory=list)
    notes: list[ContextPackItemResponse] = Field(default_factory=list)


class ContextPackResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID | None
    generated_at: datetime
    items: ContextPackItemsResponse
    warnings: list[ContextPackWarningResponse]
