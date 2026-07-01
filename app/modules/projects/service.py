from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.pagination import PageInfo
from app.modules.auth.types import ActorContext
from app.modules.authorization.service import AuthorizationService
from app.modules.memory_entries.models import MemoryEntry
from app.modules.memory_entries.repository import MemoryEntryRepository
from app.modules.projects.repository import ProjectsRepository
from app.modules.projects.schemas import (
    ProjectListResponse,
    ProjectSummaryResponse,
    ProjectTimelineEventResponse,
    ProjectTimelineResponse,
)


class ProjectService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._authorization = AuthorizationService(db)
        self._memory_repository = MemoryEntryRepository(db)
        self._projects_repository = ProjectsRepository(db)

    def list_readable_projects(
        self, *, actor: ActorContext, limit: int = 50
    ) -> ProjectListResponse:
        is_org_admin = self._authorization.can_administer_organization(actor)
        summaries: list[ProjectSummaryResponse] = []
        for project in self._projects_repository.list_projects(org_id=actor.org_id):
            effective_role = self._authorization.get_effective_project_role(actor, project.id)
            if effective_role is None and not is_org_admin:
                continue
            summaries.append(
                ProjectSummaryResponse(
                    id=project.id,
                    key=project.key,
                    name=project.name,
                    description=project.description,
                    status=project.status,
                    owning_group_id=project.owning_group_id,
                    effective_role=effective_role,
                )
            )
        summaries.sort(key=lambda summary: summary.key)
        visible = summaries[:limit]
        return ProjectListResponse(
            items=visible,
            page=PageInfo(next_cursor=None, has_more=len(summaries) > limit),
        )

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
