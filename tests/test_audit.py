from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import NotFoundError
from app.modules.audit.models import AuditDecision, AuditEvent
from app.modules.memory_entries.service import MemoryEntryService
from app.modules.search.schemas import SearchRequest
from app.modules.search.service import SearchService
from tests.conftest import SeedData, actor, memory_request


def test_create_memory_emits_safe_audit_event(db: Session, seed: SeedData) -> None:
    created = MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.morgan.id, request_id="req-create"),
        request=memory_request(),
    )
    event = db.execute(
        select(AuditEvent).where(
            AuditEvent.action == "memory_entry.created", AuditEvent.resource_id == created.id
        )
    ).scalar_one()
    assert event.org_id == seed.org.id
    assert event.actor_user_id == seed.morgan.id
    assert event.request_id == "req-create"
    assert "body" not in event.metadata_


def test_authorization_denial_emits_audit_event(db: Session, seed: SeedData) -> None:
    created = MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.morgan.id), request=memory_request()
    )
    with pytest.raises(NotFoundError):
        MemoryEntryService(db).get_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.riley.id), memory_id=created.id
        )
    event = db.execute(
        select(AuditEvent).where(AuditEvent.action == "authorization.denied")
    ).scalar_one()
    assert event.decision == AuditDecision.deny


def test_search_audit_metadata_excludes_raw_query(db: Session, seed: SeedData) -> None:
    SearchService(db).search(
        actor=actor(org_id=seed.org.id, user_id=seed.morgan.id),
        request=SearchRequest(query="secret customer payment issue", limit=10),
    )
    event = db.execute(
        select(AuditEvent).where(AuditEvent.action == "search.executed")
    ).scalar_one()
    assert "query_hash" in event.metadata_
    assert "secret customer payment issue" not in str(event.metadata_)
