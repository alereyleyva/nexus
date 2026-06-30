from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.memory_entries.models import VisibilityScope
from app.modules.memory_entries.service import MemoryEntryService
from app.modules.projects.models import ProjectRole
from app.modules.projects.service import ProjectService
from tests.conftest import SeedData, actor, add_project_membership, memory_request


def test_timeline_only_returns_authorized_project_memory_events(
    db: Session, seed: SeedData
) -> None:
    add_project_membership(
        db,
        org_id=seed.org.id,
        project_id=seed.project.id,
        user_id=seed.fabio.id,
        role=ProjectRole.reviewer,
    )
    service = MemoryEntryService(db)
    visible = service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id),
        request=memory_request(
            visibility_scope=VisibilityScope.project,
            project_id=seed.project.id,
        ),
    )
    service.create_memory(
        actor=actor(org_id=seed.org.id, user_id=seed.pablo.id),
        request=memory_request(project_id=seed.project.id, title="Private project note"),
    )
    timeline = ProjectService(db).timeline(
        actor=actor(org_id=seed.org.id, user_id=seed.fabio.id), project_id=seed.project.id
    )
    assert [event.memory_entry_id for event in timeline.events] == [visible.id]
