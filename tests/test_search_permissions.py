from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.memory_entries.models import MemoryEntry, MemoryStatus
from app.modules.memory_entries.service import MemoryEntryService
from app.modules.projects.models import ProjectRole
from app.modules.search.schemas import SearchRequest
from app.modules.search.service import SearchService
from tests.conftest import SeedData, actor, add_project_membership, memory_request


def test_search_finds_authorized_memory_by_title_body_rationale_and_tags(
    db: Session, seed: SeedData
) -> None:
    service = MemoryEntryService(db)
    service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    search = SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=SearchRequest(query="retry path", tags=["payments"], limit=10),
    )
    assert len(search.results) == 1
    assert search.results[0].needs_review_warning is False


def test_search_does_not_return_private_memory_owned_by_another_user(
    db: Session, seed: SeedData
) -> None:
    MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    search = SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        request=SearchRequest(query="payment", limit=10),
    )
    assert search.results == []


def test_search_project_filter_does_not_bypass_private_visibility(
    db: Session, seed: SeedData
) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.fabio.id,
        role=ProjectRole.maintainer,
    )
    MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(project_id=seed.project.id),
    )
    search = SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        request=SearchRequest(query="payment", project_id=seed.project.id, limit=10),
    )
    assert search.results == []


def test_search_excludes_hidden_statuses_by_default_and_allows_deprecated_explicitly(
    db: Session, seed: SeedData
) -> None:
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    memory = db.execute(select(MemoryEntry).where(MemoryEntry.id == created.id)).scalar_one()
    memory.status = MemoryStatus.deprecated
    db.commit()
    default_search = SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=SearchRequest(query="payment", limit=10),
    )
    explicit_search = SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=SearchRequest(query="payment", statuses=[MemoryStatus.deprecated], limit=10),
    )
    assert default_search.results == []
    assert [result.id for result in explicit_search.results] == [created.id]


def test_search_audit_stores_hash_instead_of_raw_query(db: Session, seed: SeedData) -> None:
    SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=SearchRequest(query="secret customer payment issue", limit=10),
    )
    event = db.execute(
        select(AuditEvent).where(AuditEvent.action == "search.executed")
    ).scalar_one()
    assert "query_hash" in event.metadata_
    assert "secret customer payment issue" not in str(event.metadata_)


def test_search_returns_needs_review_memory_with_warning_marker(
    db: Session, seed: SeedData
) -> None:
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    memory = db.execute(select(MemoryEntry).where(MemoryEntry.id == created.id)).scalar_one()
    memory.status = MemoryStatus.needs_review
    db.commit()
    search = SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=SearchRequest(query="payment", statuses=[MemoryStatus.needs_review], limit=10),
    )
    assert search.results[0].status == MemoryStatus.needs_review
    assert search.results[0].needs_review_warning is True
