from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.json import JsonObject
from app.common.pagination import PageInfo
from app.modules.memory_entries.models import (
    EvidenceKind,
    GrantRole,
    MemoryStatus,
    MemoryType,
    SourceKind,
    VisibilityScope,
)


class CreateEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: EvidenceKind
    title: str | None = None
    quote: str | None = None
    url: str | None = None
    locator: JsonObject = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)


class CreateMemoryEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID | None = None
    type: MemoryType
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    rationale: str | None = None
    visibility_scope: VisibilityScope | None = None
    visibility_group_id: UUID | None = None
    source_kind: SourceKind = SourceKind.api
    source_tool: str = Field(min_length=1)
    source_ref: str | None = None
    client_entry_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    source_context: JsonObject = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)
    evidence: list[CreateEvidenceRequest] = Field(default_factory=list)


class BulkCreateMemoryEntriesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[CreateMemoryEntryRequest] = Field(min_length=1, max_length=100)


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: EvidenceKind
    title: str | None
    quote: str | None
    url: str | None
    locator: JsonObject
    metadata: JsonObject = Field(validation_alias="metadata_")
    created_at: datetime


class MemoryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    project_id: UUID | None
    owner_user_id: UUID
    created_by_user_id: UUID
    submitted_via_session_id: UUID | None
    type: MemoryType
    title: str
    body: str
    rationale: str | None
    status: MemoryStatus
    visibility_scope: VisibilityScope
    visibility_group_id: UUID | None
    source_kind: SourceKind
    source_tool: str
    source_ref: str | None
    client_entry_id: str | None
    confidence: float | None
    tags: list[str]
    source_context: JsonObject
    metadata: JsonObject = Field(validation_alias="metadata_")
    reviewed_by_user_id: UUID | None
    review_comment: str | None
    reviewed_at: datetime | None
    review_after: datetime | None
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0
    needs_review_warning: bool = False
    evidence: list[EvidenceResponse] = Field(default_factory=list)


class MemoryMutationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: MemoryStatus
    visibility_scope: VisibilityScope
    requires_review: bool


class BulkCreateMemoryEntriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[MemoryMutationResponse]


class MemoryEntryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[MemoryEntryResponse]
    page: PageInfo


class UpdateMemoryEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    body: str | None = None
    rationale: str | None = None
    tags: list[str] | None = None
    metadata: JsonObject | None = None
    source_context: JsonObject | None = None


class ReviewMemoryEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject"]
    review_comment: str | None = None


class LifecycleReasonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


class ChangeVisibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visibility_scope: VisibilityScope
    project_id: UUID | None = None
    visibility_group_id: UUID | None = None
    reason: str | None = None


class AddGrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grantee_user_id: UUID
    role: GrantRole


class GrantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grantee_user_id: UUID
    role: GrantRole
    created_by_user_id: UUID
    created_at: datetime
