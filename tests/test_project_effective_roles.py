from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.authorization.service import AuthorizationService
from app.modules.groups.models import Group, GroupRole, GroupType
from app.modules.projects.models import Project, ProjectRole, ProjectStatus
from tests.conftest import SeedData, actor, add_group_membership, add_project_membership


def test_owning_group_member_derives_contributor_role(db: Session, seed: SeedData) -> None:
    add_group_membership(
        db, org_id=seed.org.id, group_id=seed.group.id, user_id=seed.pablo.id, role=GroupRole.member
    )
    role = AuthorizationService(db).get_effective_project_role(
        actor(org_id=seed.org.id, user_id=seed.pablo.id), seed.project.id
    )
    assert role == ProjectRole.contributor


def test_owning_group_lead_derives_maintainer_role(db: Session, seed: SeedData) -> None:
    add_group_membership(
        db, org_id=seed.org.id, group_id=seed.group.id, user_id=seed.fabio.id, role=GroupRole.lead
    )
    role = AuthorizationService(db).get_effective_project_role(
        actor(org_id=seed.org.id, user_id=seed.fabio.id), seed.project.id
    )
    assert role == ProjectRole.maintainer


def test_highest_project_role_wins_across_inherited_and_explicit(
    db: Session, seed: SeedData
) -> None:
    add_group_membership(
        db, org_id=seed.org.id, group_id=seed.group.id, user_id=seed.pablo.id, role=GroupRole.member
    )
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.pablo.id,
        role=ProjectRole.reviewer,
    )
    role = AuthorizationService(db).get_effective_project_role(
        actor(org_id=seed.org.id, user_id=seed.pablo.id), seed.project.id
    )
    assert role == ProjectRole.reviewer


def test_parent_group_does_not_grant_permissions(db: Session, seed: SeedData) -> None:
    parent = Group(
        org_id=seed.org.id, slug="engineering", name="Engineering", group_type=GroupType.department
    )
    db.add(parent)
    db.flush()
    seed.group.parent_group_id = parent.id
    project = Project(
        org_id=seed.org.id,
        owning_group_id=seed.group.id,
        key="PARENT",
        name="Parent Test",
        status=ProjectStatus.active,
    )
    db.add(project)
    db.commit()
    add_group_membership(
        db, org_id=seed.org.id, group_id=parent.id, user_id=seed.carlos.id, role=GroupRole.lead
    )
    role = AuthorizationService(db).get_effective_project_role(
        actor(org_id=seed.org.id, user_id=seed.carlos.id), project.id
    )
    assert role is None
