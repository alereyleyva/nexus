from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.ids import new_uuid
from app.common.time import utc_now
from app.db.base import Base


class GroupType(StrEnum):
    team = "team"
    department = "department"
    squad = "squad"
    area = "area"


class GroupRole(StrEnum):
    member = "member"
    lead = "lead"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    slug: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    group_type: Mapped[GroupType] = mapped_column(
        Enum(GroupType, name="group_type", native_enum=False), nullable=False
    )
    parent_group_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("org_id", "slug", name="groups_org_slug_unique"),
        UniqueConstraint("org_id", "id", name="groups_org_id_unique"),
    )


class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    group_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("groups.id"))
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    role: Mapped[GroupRole] = mapped_column(
        Enum(GroupRole, name="group_role", native_enum=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="group_memberships_group_user_unique"),
        Index("group_memberships_user_idx", "org_id", "user_id"),
        Index("group_memberships_group_idx", "org_id", "group_id"),
    )
