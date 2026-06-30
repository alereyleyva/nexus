from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.groups.models import GroupRole, GroupType
from app.modules.identity.models import OrgRole, UserStatus
from app.modules.projects.models import ProjectRole, ProjectStatus


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3)
    display_name: str = Field(min_length=1)
    status: UserStatus = UserStatus.active
    role: OrgRole = OrgRole.member
    is_org_admin: bool = False


class UpdateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    status: UserStatus | None = None


class UserAdminResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: str
    display_name: str
    status: UserStatus
    role: OrgRole
    is_org_admin: bool


class UsersAdminResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[UserAdminResponse]


class SetOrgMembershipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: OrgRole
    is_org_admin: bool


class CreateGroupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str
    group_type: GroupType = GroupType.team
    parent_group_id: UUID | None = None


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    group_type: GroupType
    parent_group_id: UUID | None


class GroupsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[GroupResponse]


class SetGroupMembershipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: GroupRole


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owning_group_id: UUID
    key: str
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.active


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owning_group_id: UUID
    key: str
    name: str
    description: str | None
    status: ProjectStatus


class ProjectsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProjectResponse]


class SetProjectMembershipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: ProjectRole
