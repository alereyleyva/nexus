from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.pagination import PageInfo
from app.modules.auth.types import ActorContext
from app.modules.authorization.service import AuthorizationService
from app.modules.memory_entries.models import MemoryEntry
from app.modules.memory_entries.repository import MemoryEntryRepository
from app.modules.projects.schemas import ProjectTimelineEventResponse, ProjectTimelineResponse


class ProjectService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._authorization = AuthorizationService(db)
        self._memory_repository = MemoryEntryRepository(db)

    def timeline(
        self, *, actor: ActorContext, project_id: UUID, limit: int = 50
    ) -> ProjectTimelineResponse:
        statement = (
            self._authorization.readable_memory_statement(actor)
            .where(MemoryEntry.project_id == project_id)
            .order_by(MemoryEntry.updated_at.desc(), MemoryEntry.id.desc())
        )
        memories = self._memory_repository.list_by_statement(statement, limit=limit + 1)
        visible = memories[:limit]
        return ProjectTimelineResponse(
            project_id=project_id,
            events=[
                ProjectTimelineEventResponse(
                    timestamp=memory.updated_at,
                    event_type="memory_entry.created",
                    memory_entry_id=memory.id,
                    type=memory.type,
                    title=memory.title,
                )
                for memory in visible
            ],
            page=PageInfo(next_cursor=None, has_more=len(memories) > limit),
        )
