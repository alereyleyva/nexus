from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.groups.models import GroupMembership
from app.modules.projects.models import Project, ProjectMembership


class ProjectsRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add_project(self, project: Project) -> Project:
        self._db.add(project)
        return project

    def add_membership(self, membership: ProjectMembership) -> ProjectMembership:
        self._db.add(membership)
        return membership

    def delete_membership(self, membership: ProjectMembership) -> None:
        self._db.delete(membership)

    def get_project(self, *, org_id: UUID, project_id: UUID) -> Project | None:
        return self._db.execute(
            select(Project).where(Project.org_id == org_id, Project.id == project_id)
        ).scalar_one_or_none()

    def list_projects(self, *, org_id: UUID) -> list[Project]:
        return list(
            self._db.execute(
                select(Project).where(Project.org_id == org_id).order_by(Project.created_at.desc())
            )
            .scalars()
            .all()
        )

    def get_membership(
        self, *, org_id: UUID, project_id: UUID, user_id: UUID
    ) -> ProjectMembership | None:
        return self._db.execute(
            select(ProjectMembership).where(
                ProjectMembership.org_id == org_id,
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == user_id,
            )
        ).scalar_one_or_none()

    def list_effective_project_ids(self, *, org_id: UUID, user_id: UUID) -> list[UUID]:
        explicit = select(ProjectMembership.project_id).where(
            ProjectMembership.org_id == org_id,
            ProjectMembership.user_id == user_id,
        )
        inherited = (
            select(Project.id)
            .join(GroupMembership, GroupMembership.group_id == Project.owning_group_id)
            .where(GroupMembership.org_id == org_id, GroupMembership.user_id == user_id)
        )
        return list(self._db.execute(explicit.union(inherited)).scalars().all())
