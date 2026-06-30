from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.ids import new_uuid
from app.common.json import JsonObject
from app.common.time import utc_now
from app.db.base import Base
from app.db.types import JSON_OBJECT, SEARCH_VECTOR, STRING_LIST


class VisibilityScope(StrEnum):
    private = "private"
    restricted = "restricted"
    group = "group"
    project = "project"
    organization = "organization"


VISIBILITY_LEVELS: dict[VisibilityScope, int] = {
    VisibilityScope.private: 10,
    VisibilityScope.restricted: 20,
    VisibilityScope.group: 30,
    VisibilityScope.project: 40,
    VisibilityScope.organization: 50,
}


class MemoryType(StrEnum):
    decision = "decision"
    problem = "problem"
    solution = "solution"
    failed_attempt = "failed_attempt"
    procedure = "procedure"
    risk = "risk"
    open_question = "open_question"
    task = "task"
    note = "note"


class MemoryStatus(StrEnum):
    pending_review = "pending_review"
    active = "active"
    needs_review = "needs_review"
    rejected = "rejected"
    deprecated = "deprecated"
    archived = "archived"


class SourceKind(StrEnum):
    ai_cli = "ai_cli"
    manual = "manual"
    api = "api"
    future_integration = "future_integration"


class GrantRole(StrEnum):
    viewer = "viewer"
    editor = "editor"
    manager = "manager"


class EvidenceKind(StrEnum):
    quote = "quote"
    code_reference = "code_reference"
    document_reference = "document_reference"
    meeting_note = "meeting_note"
    chat_message = "chat_message"
    url = "url"
    ticket = "ticket"
    pull_request = "pull_request"
    commit = "commit"
    manual_note = "manual_note"


DEFAULT_READ_STATUSES: tuple[MemoryStatus, MemoryStatus] = (
    MemoryStatus.active,
    MemoryStatus.needs_review,
)


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    project_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    owner_user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    created_by_user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    submitted_via_session_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType, name="memory_type", native_enum=False), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MemoryStatus] = mapped_column(
        Enum(MemoryStatus, name="memory_status", native_enum=False), nullable=False
    )
    visibility_scope: Mapped[VisibilityScope] = mapped_column(
        Enum(VisibilityScope, name="memory_visibility_scope", native_enum=False), nullable=False
    )
    visibility_group_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    source_kind: Mapped[SourceKind] = mapped_column(
        Enum(SourceKind, name="source_kind", native_enum=False), nullable=False
    )
    source_tool: Mapped[str] = mapped_column(String, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    client_entry_id: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    tags: Mapped[list[str]] = mapped_column(STRING_LIST, default=list)
    source_context: Mapped[JsonObject] = mapped_column(JSON_OBJECT, default=dict)
    metadata_: Mapped[JsonObject] = mapped_column("metadata", JSON_OBJECT, default=dict)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    search_vector: Mapped[str | None] = mapped_column(SEARCH_VECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "confidence is null or (confidence >= 0 and confidence <= 1)",
            name="memory_entries_confidence_range",
        ),
        CheckConstraint(
            "(visibility_scope = 'group' and visibility_group_id is not null) or "
            "(visibility_scope != 'group' and visibility_group_id is null)",
            name="memory_entries_group_visibility_shape",
        ),
        CheckConstraint(
            "visibility_scope != 'project' or project_id is not null",
            name="memory_entries_project_visibility_requires_project",
        ),
        Index("memory_entries_org_id_unique", "org_id", "id", unique=True),
        Index("memory_entries_org_project_idx", "org_id", "project_id"),
        Index("memory_entries_status_idx", "org_id", "status"),
        Index("memory_entries_visibility_idx", "org_id", "visibility_scope"),
        Index("memory_entries_owner_idx", "org_id", "owner_user_id"),
        Index("memory_entries_group_visibility_idx", "org_id", "visibility_group_id"),
        Index("memory_entries_source_ref_idx", "org_id", "source_tool", "source_ref"),
        Index(
            "memory_entries_client_entry_id_unique",
            "org_id",
            "created_by_user_id",
            "source_tool",
            "client_entry_id",
            unique=True,
        ),
    )


class MemoryEntryGrant(Base):
    __tablename__ = "memory_entry_grants"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    memory_entry_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("memory_entries.id")
    )
    grantee_user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    role: Mapped[GrantRole] = mapped_column(
        Enum(GrantRole, name="grant_role", native_enum=False), nullable=False
    )
    created_by_user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index(
            "memory_entry_grants_entry_grantee_unique",
            "memory_entry_id",
            "grantee_user_id",
            unique=True,
        ),
        Index("memory_entry_grants_grantee_idx", "org_id", "grantee_user_id"),
    )


class MemoryEntryEvidence(Base):
    __tablename__ = "memory_entry_evidence"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    memory_entry_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("memory_entries.id")
    )
    kind: Mapped[EvidenceKind] = mapped_column(
        Enum(EvidenceKind, name="evidence_kind", native_enum=False), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    locator: Mapped[JsonObject] = mapped_column(JSON_OBJECT, default=dict)
    metadata_: Mapped[JsonObject] = mapped_column("metadata", JSON_OBJECT, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (Index("memory_entry_evidence_entry_idx", "org_id", "memory_entry_id"),)
