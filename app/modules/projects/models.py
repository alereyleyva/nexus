from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.ids import new_uuid
from app.common.time import utc_now
from app.db.base import Base


class ProjectStatus(StrEnum):
    active = "active"
    archived = "archived"


class ProjectRole(StrEnum):
    viewer = "viewer"
    contributor = "contributor"
    reviewer = "reviewer"
    maintainer = "maintainer"


PROJECT_ROLE_LEVELS: dict[ProjectRole, int] = {
    ProjectRole.viewer: 10,
    ProjectRole.contributor: 20,
    ProjectRole.reviewer: 30,
    ProjectRole.maintainer: 40,
}


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    owning_group_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("groups.id"))
    key: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("org_id", "key", name="projects_org_key_unique"),
        UniqueConstraint("org_id", "id", name="projects_org_id_unique"),
        Index("projects_org_group_idx", "org_id", "owning_group_id"),
    )


class ProjectMembership(Base):
    __tablename__ = "project_memberships"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id"))
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_role", native_enum=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="project_memberships_project_user_unique"),
        Index("project_memberships_user_idx", "org_id", "user_id"),
        Index("project_memberships_project_idx", "org_id", "project_id"),
    )
