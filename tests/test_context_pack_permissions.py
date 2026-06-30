from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.context_packs.schemas import ContextPackRequest
from app.modules.context_packs.service import ContextPackService
from app.modules.memory_entries.models import MemoryEntry, MemoryStatus, MemoryType
from app.modules.memory_entries.service import MemoryEntryService
from app.modules.projects.models import ProjectRole
from tests.conftest import SeedData, actor, add_project_membership, memory_request


def test_context_pack_groups_authorized_memory_by_type(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(title="Decision payment", body="payment", tags=["payments"]),
    )
    problem = memory_request(title="Problem payment", body="payment", tags=["payments"])
    problem.type = MemoryType.problem
    service.create_memory(actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=problem)
    pack = ContextPackService(db).generate(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=ContextPackRequest(query="payment", max_items=20),
    )
    assert len(pack.items.decisions) == 1
    assert len(pack.items.problems) == 1


def test_context_pack_respects_max_items(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    for index in range(5):
        service.create_memory(
            actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
            request=memory_request(title=f"Decision {index} payment", body="payment"),
        )
    pack = ContextPackService(db).generate(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=ContextPackRequest(query="payment", max_items=3),
    )
    total = sum(len(group) for group in pack.items.model_dump().values())
    assert total <= 3


def test_context_pack_excludes_unauthorized_private_memory(db: Session, seed: SeedData) -> None:
    MemoryEntryService(db).create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    pack = ContextPackService(db).generate(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        request=ContextPackRequest(query="payment", max_items=20),
    )
    assert pack.items.decisions == []


def test_context_pack_project_filter_does_not_bypass_visibility(
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
    pack = ContextPackService(db).generate(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        request=ContextPackRequest(project_id=seed.project.id, query="payment", max_items=20),
    )
    assert pack.items.decisions == []


def test_context_pack_includes_needs_review_warning_and_audit(db: Session, seed: SeedData) -> None:
    service = MemoryEntryService(db)
    created = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id), request=memory_request()
    )
    memory = db.execute(select(MemoryEntry).where(MemoryEntry.id == created.id)).scalar_one()
    memory.status = MemoryStatus.needs_review
    db.commit()
    pack = ContextPackService(db).generate(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=ContextPackRequest(query="payment", max_items=20),
    )
    event = db.execute(
        select(AuditEvent).where(AuditEvent.action == "context_pack.generated")
    ).scalar_one()
    assert pack.warnings[0].type == "needs_review"
    assert event.action == "context_pack.generated"
