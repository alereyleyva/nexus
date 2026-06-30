from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import ConflictError, NotFoundError
from app.modules.groups.models import GroupRole
from app.modules.identity.models import OrgMembership, OrgRole
from app.modules.memory_entries.models import GrantRole, MemoryEntry, MemoryStatus, VisibilityScope
from app.modules.memory_entries.schemas import AddGrantRequest
from app.modules.memory_entries.service import MemoryEntryService
from app.modules.projects.models import ProjectRole
from tests.conftest import (
    SeedData,
    actor,
    add_group_membership,
    add_project_membership,
    memory_request,
)


def test_private_memory_is_readable_by_owner(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    response = service.get_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), memory_id=created.id
    )
    assert response.id == created.id


def test_org_admin_cannot_read_private_memory_owned_by_another_user(
    db: Session, seed: SeedData
) -> None:
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    admin_actor = actor(org_id=seed.org.id, user_id=seed.fabio.id)
    membership = db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == seed.org.id,
            OrgMembership.user_id == seed.fabio.id,
        )
    ).scalar_one()
    membership.role = OrgRole.member
    membership.is_org_admin = True
    db.commit()
    with pytest.raises(NotFoundError):
        service.get_memory(actor=admin_actor, memory_id=created.id)


def test_restricted_memory_is_readable_by_explicit_grantee(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    owner = actor(org_id=seed.org.id, user_id=seed.pablo.id)
    created = service.create_memory(
        actor=owner,
        request=memory_request(visibility_scope=VisibilityScope.restricted),
    )
    service.add_grant(
        actor=owner,
        memory_id=created.id,
        request=AddGrantRequest(grantee_user_id=seed.fabio.id, role=GrantRole.viewer),
    )
    response = service.get_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id), memory_id=created.id
    )
    assert response.id == created.id


def test_duplicate_grant_conflicts_and_removal_revokes_access(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    owner = actor(org_id=seed.org.id, user_id=seed.pablo.id)
    created = service.create_memory(
        actor=owner,
        request=memory_request(visibility_scope=VisibilityScope.restricted),
    )
    grant = service.add_grant(
        actor=owner,
        memory_id=created.id,
        request=AddGrantRequest(grantee_user_id=seed.fabio.id, role=GrantRole.viewer),
    )
    with pytest.raises(ConflictError):
        service.add_grant(
            actor=owner,
            memory_id=created.id,
            request=AddGrantRequest(grantee_user_id=seed.fabio.id, role=GrantRole.viewer),
        )
    service.delete_grant(actor=owner, memory_id=created.id, grant_id=grant.id)
    with pytest.raises(NotFoundError):
        service.get_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.fabio.id), memory_id=created.id
        )


def test_project_association_does_not_imply_project_visibility(db: Session, seed: SeedData) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.fabio.id,
        role=ProjectRole.maintainer,
    )
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(project_id=seed.project.id),
    )
    with pytest.raises(NotFoundError):
        service.get_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.fabio.id), memory_id=created.id
        )


def test_group_and_project_memory_require_membership(db: Session, seed: SeedData) -> None:
    add_group_membership(
        db, org_id=seed.org.id, group_id=seed.group.id, user_id=seed.pablo.id, role=GroupRole.lead
    )
    service = MemoryEntryService(db)
    group_memory = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(
            visibility_scope=VisibilityScope.group, visibility_group_id=seed.group.id
        ),
    )
    with pytest.raises(NotFoundError):
        service.get_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.carlos.id), memory_id=group_memory.id
        )


def test_normal_reads_hide_non_default_statuses(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    memory = db.execute(select(MemoryEntry).where(MemoryEntry.id == created.id)).scalar_one()
    memory.status = MemoryStatus.deprecated
    db.commit()
    with pytest.raises(NotFoundError):
        service.get_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), memory_id=created.id
        )
