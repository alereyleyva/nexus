from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.ids import new_uuid
from app.common.json import JsonObject
from app.common.time import utc_now
from app.db.base import Base
from app.db.types import JSON_OBJECT


class AuditDecision(StrEnum):
    allow = "allow"
    deny = "deny"


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    actor_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    actor_session_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String, nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    decision: Mapped[AuditDecision | None] = mapped_column(
        Enum(AuditDecision, name="audit_decision", native_enum=False), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_: Mapped[JsonObject] = mapped_column("metadata", JSON_OBJECT, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("audit_events_org_created_idx", "org_id", "created_at"),
        Index("audit_events_resource_idx", "org_id", "resource_type", "resource_id"),
    )
