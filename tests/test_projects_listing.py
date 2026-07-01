from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.groups.models import GroupRole
from app.modules.projects.models import ProjectRole
from app.modules.projects.service import ProjectService
from tests.conftest import (
    SeedData,
    actor,
    add_group_membership,
    add_project_membership,
)


def test_lists_projects_with_effective_role(db: Session, seed: SeedData) -> None:
    add_group_membership(
        db, org_id=seed.org.id, group_id=seed.group.id, user_id=seed.pablo.id, role=GroupRole.lead
    )
    response = ProjectService(db).list_readable_projects(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id)
    )
    assert [item.key for item in response.items] == ["CECW"]
    assert response.items[0].effective_role == ProjectRole.maintainer


def test_hides_projects_without_effective_role(db: Session, seed: SeedData) -> None:
    response = ProjectService(db).list_readable_projects(
        actor=actor(org_id=seed.org.id, user_id=seed.carlos.id)
    )
    assert response.items == []


def test_explicit_membership_exposes_project(db: Session, seed: SeedData) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.carlos.id,
        role=ProjectRole.viewer,
    )
    response = ProjectService(db).list_readable_projects(
        actor=actor(org_id=seed.org.id, user_id=seed.carlos.id)
    )
    assert [item.key for item in response.items] == ["CECW"]
    assert response.items[0].effective_role == ProjectRole.viewer


def test_other_org_actor_sees_no_projects(db: Session, seed: SeedData) -> None:
    response = ProjectService(db).list_readable_projects(
        actor=actor(org_id=seed.other_org.id, user_id=seed.pablo.id)
    )
    assert response.items == []
