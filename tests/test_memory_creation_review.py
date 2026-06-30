from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import AuthorizationDeniedError
from app.modules.groups.models import GroupRole
from app.modules.memory_entries.models import MemoryEntry, MemoryStatus, VisibilityScope
from app.modules.memory_entries.schemas import (
    BulkCreateMemoryEntriesRequest,
    ChangeVisibilityRequest,
    ReviewMemoryEntryRequest,
    UpdateMemoryEntryRequest,
)
from app.modules.memory_entries.service import MemoryEntryService
from app.modules.projects.models import ProjectRole
from tests.conftest import (
    SeedData,
    actor,
    add_group_membership,
    add_project_membership,
    memory_request,
)


def test_missing_visibility_defaults_to_private_active_memory(db: Session, seed: SeedData) -> None:
    result = MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(),
    )
    assert result.visibility_scope == VisibilityScope.private
    assert result.status == MemoryStatus.active
    assert result.requires_review is False


def test_group_member_proposes_group_memory_for_review(db: Session, seed: SeedData) -> None:
    add_group_membership(
        db, org_id=seed.org.id, group_id=seed.group.id, user_id=seed.pablo.id, role=GroupRole.member
    )
    result = MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(
            visibility_scope=VisibilityScope.group, visibility_group_id=seed.group.id
        ),
    )
    assert result.status == MemoryStatus.pending_review
    assert result.requires_review is True


def test_project_reviewer_creates_project_memory_as_active(db: Session, seed: SeedData) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.fabio.id,
        role=ProjectRole.reviewer,
    )
    result = MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        request=memory_request(
            visibility_scope=VisibilityScope.project, project_id=seed.project.id
        ),
    )
    assert result.status == MemoryStatus.active
    assert result.requires_review is False


def test_creator_cannot_self_review_shared_memory(db: Session, seed: SeedData) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.pablo.id,
        role=ProjectRole.reviewer,
    )
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(
            visibility_scope=VisibilityScope.project,
            project_id=seed.project.id,
        ),
    )
    memory = db.execute(select(MemoryEntry).where(MemoryEntry.id == created.id)).scalar_one()
    memory.status = MemoryStatus.pending_review
    db.commit()
    with pytest.raises(AuthorizationDeniedError):
        service.review_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
            memory_id=created.id,
            request=ReviewMemoryEntryRequest(decision="approve", review_comment="self"),
        )


def test_project_reviewer_approves_project_memory(db: Session, seed: SeedData) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.pablo.id,
        role=ProjectRole.contributor,
    )
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.fabio.id,
        role=ProjectRole.reviewer,
    )
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(
            visibility_scope=VisibilityScope.project, project_id=seed.project.id
        ),
    )
    reviewed = service.review_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        memory_id=created.id,
        request=ReviewMemoryEntryRequest(decision="approve", review_comment="valid"),
    )
    assert reviewed.status == MemoryStatus.active


def test_project_contributor_cannot_edit_active_approved_project_memory(
    db: Session, seed: SeedData
) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.fabio.id,
        role=ProjectRole.reviewer,
    )
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.pablo.id,
        role=ProjectRole.contributor,
    )
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        request=memory_request(
            visibility_scope=VisibilityScope.project, project_id=seed.project.id
        ),
    )
    with pytest.raises(AuthorizationDeniedError):
        service.update_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
            memory_id=created.id,
            request=UpdateMemoryEntryRequest(body="unsafe rewrite"),
        )


def test_bulk_create_creates_independent_entries_atomically(db: Session, seed: SeedData) -> None:
    response = MemoryEntryService(db).bulk_create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=BulkCreateMemoryEntriesRequest(
            entries=[memory_request(), memory_request(title="Second")]
        ),
    )
    assert len(response.items) == 2
    assert {item.status for item in response.items} == {MemoryStatus.active}


def test_owner_updates_private_memory_and_refreshes_search_document(
    db: Session, seed: SeedData
) -> None:
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    updated = service.update_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        memory_id=created.id,
        request=UpdateMemoryEntryRequest(title="Updated idempotency", tags=["updated"]),
    )
    memory = db.execute(select(MemoryEntry).where(MemoryEntry.id == created.id)).scalar_one()
    assert updated.title == "Updated idempotency"
    assert "updated" in (memory.search_vector or "")


def test_private_memory_visibility_lifecycle_and_delete(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    owner = actor(org_id=seed.org.id, user_id=seed.pablo.id)
    created = service.create_memory(actor=owner, request=memory_request())
    restricted = service.change_visibility(
        actor=owner,
        memory_id=created.id,
        request=ChangeVisibilityRequest(visibility_scope=VisibilityScope.restricted),
    )
    needs_review = service.mark_needs_review(actor=owner, memory_id=created.id, reason="freshness")
    deprecated = service.deprecate_memory(actor=owner, memory_id=created.id, reason="superseded")
    archived = service.archive_memory(actor=owner, memory_id=created.id, reason="historical")
    private_created = service.create_memory(actor=owner, request=memory_request(title="Delete me"))
    service.soft_delete_memory(actor=owner, memory_id=private_created.id)
    deleted = db.execute(
        select(MemoryEntry).where(MemoryEntry.id == private_created.id)
    ).scalar_one()
    assert restricted.visibility_scope == VisibilityScope.restricted
    assert needs_review.status == MemoryStatus.needs_review
    assert deprecated.status == MemoryStatus.deprecated
    assert archived.status == MemoryStatus.archived
    assert deleted.deleted_at is not None


def test_review_queue_returns_only_reviewable_memory(db: Session, seed: SeedData) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.pablo.id,
        role=ProjectRole.contributor,
    )
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.fabio.id,
        role=ProjectRole.reviewer,
    )
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(
            visibility_scope=VisibilityScope.project, project_id=seed.project.id
        ),
    )
    queue = service.review_queue(actor=actor(org_id=seed.org.id, user_id=seed.fabio.id))
    assert [item.id for item in queue.items] == [created.id]
