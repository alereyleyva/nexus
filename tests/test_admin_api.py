from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import AuthorizationDeniedError, ConflictError, NotFoundError
from app.modules.admin.schemas import (
    CreateGroupRequest,
    CreateProjectRequest,
    CreateUserRequest,
    SetGroupMembershipRequest,
    SetOrgMembershipRequest,
    SetProjectMembershipRequest,
    UpdateUserRequest,
)
from app.modules.admin.service import AdminService
from app.modules.groups.models import GroupRole, GroupType
from app.modules.identity.models import OrgMembership, OrgRole
from app.modules.memory_entries.service import MemoryEntryService
from app.modules.projects.models import ProjectMembership, ProjectRole, ProjectStatus
from tests.conftest import SeedData, actor, memory_request


def test_org_admin_configures_project_membership(db: Session, seed: SeedData) -> None:
    make_org_admin(db, seed)
    AdminService(db).set_project_membership(
        actor=actor(org_id=seed.org.id, user_id=seed.morgan.id),
        project_id=seed.project.id,
        user_id=seed.riley.id,
        request=SetProjectMembershipRequest(role=ProjectRole.reviewer),
    )
    membership = db.execute(
        select(ProjectMembership).where(
            ProjectMembership.project_id == seed.project.id,
            ProjectMembership.user_id == seed.riley.id,
        )
    ).scalar_one()
    assert membership.role == ProjectRole.reviewer


def test_org_admin_manages_users_groups_and_projects(db: Session, seed: SeedData) -> None:
    make_org_admin(db, seed)
    service = AdminService(db)
    admin_actor = actor(org_id=seed.org.id, user_id=seed.morgan.id)
    created_user = service.create_user(
        actor=admin_actor,
        request=CreateUserRequest(
            email="jordan@example.com",
            display_name="Jordan",
            role=OrgRole.knowledge_admin,
        ),
    )
    updated_user = service.update_user(
        actor=admin_actor,
        user_id=created_user.id,
        request=UpdateUserRequest(display_name="Jordan Updated"),
    )
    group = service.create_group(
        actor=admin_actor,
        request=CreateGroupRequest(slug="platform", name="Platform", group_type=GroupType.team),
    )
    service.set_group_membership(
        actor=admin_actor,
        group_id=group.id,
        user_id=created_user.id,
        request=SetGroupMembershipRequest(role=GroupRole.lead),
    )
    project = service.create_project(
        actor=admin_actor,
        request=CreateProjectRequest(
            owning_group_id=group.id,
            key="PLAT",
            name="Platform",
            status=ProjectStatus.active,
        ),
    )
    assert updated_user.display_name == "Jordan Updated"
    assert any(item.id == created_user.id for item in service.list_users(actor=admin_actor).items)
    assert any(item.id == group.id for item in service.list_groups(actor=admin_actor).items)
    assert any(item.id == project.id for item in service.list_projects(actor=admin_actor).items)


def test_org_membership_update_enforces_last_admin_safeguard(db: Session, seed: SeedData) -> None:
    make_org_admin(db, seed)
    with pytest.raises(ConflictError):
        AdminService(db).set_org_membership(
            actor=actor(org_id=seed.org.id, user_id=seed.morgan.id),
            user_id=seed.morgan.id,
            request=SetOrgMembershipRequest(role=OrgRole.member, is_org_admin=False),
        )


def test_non_org_admin_is_denied_for_admin_endpoint(db: Session, seed: SeedData) -> None:
    with pytest.raises(AuthorizationDeniedError):
        AdminService(db).set_project_membership(
            actor=actor(org_id=seed.org.id, user_id=seed.morgan.id),
            project_id=seed.project.id,
            user_id=seed.riley.id,
            request=SetProjectMembershipRequest(role=ProjectRole.reviewer),
        )


def test_org_admin_cannot_read_another_users_private_memory(db: Session, seed: SeedData) -> None:
    make_org_admin(db, seed)
    created = MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.riley.id), request=memory_request()
    )
    with pytest.raises(NotFoundError):
        MemoryEntryService(db).get_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.morgan.id), memory_id=created.id
        )


def make_org_admin(db: Session, seed: SeedData) -> None:
    membership = db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == seed.org.id,
            OrgMembership.user_id == seed.morgan.id,
        )
    ).scalar_one()
    membership.role = OrgRole.member
    membership.is_org_admin = True
    db.commit()
