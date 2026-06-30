from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, and_, exists, false, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.common.errors import AuthorizationDeniedError, ValidationProblem
from app.modules.audit.service import AuditService
from app.modules.auth.types import ActorContext
from app.modules.groups.models import GroupMembership, GroupRole
from app.modules.identity.models import OrgMembership, OrgRole
from app.modules.identity.repository import IdentityRepository
from app.modules.memory_entries.models import (
    DEFAULT_READ_STATUSES,
    VISIBILITY_LEVELS,
    GrantRole,
    MemoryEntry,
    MemoryEntryGrant,
    MemoryStatus,
    VisibilityScope,
)
from app.modules.projects.models import PROJECT_ROLE_LEVELS, Project, ProjectMembership, ProjectRole
from app.modules.projects.repository import ProjectsRepository


@dataclass(frozen=True)
class CreationDecision:
    status: MemoryStatus
    requires_review: bool


@dataclass(frozen=True)
class VisibilityDecision:
    status: MemoryStatus
    requires_review: bool


class AuthorizationService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._identity_repository = IdentityRepository(db)
        self._projects_repository = ProjectsRepository(db)
        self._audit_service = AuditService(db)

    def require_capability(self, actor: ActorContext, capability: str) -> None:
        if actor.session_capabilities and capability not in actor.session_capabilities:
            self._audit_service.record_denial(
                actor=actor,
                reason="missing_capability",
                metadata={"capability": capability},
            )
            self._db.flush()
            raise AuthorizationDeniedError("The session is missing the required capability.")

    def get_org_membership(self, actor: ActorContext) -> OrgMembership | None:
        return self._identity_repository.get_membership(org_id=actor.org_id, user_id=actor.user_id)

    def can_administer_organization(self, actor: ActorContext) -> bool:
        membership = self.get_org_membership(actor)
        return membership is not None and membership.is_org_admin

    def get_effective_project_role(
        self, actor: ActorContext, project_id: UUID
    ) -> ProjectRole | None:
        project = self._projects_repository.get_project(org_id=actor.org_id, project_id=project_id)
        if project is None:
            return None
        candidates: list[ProjectRole] = []
        group_role = self._db.execute(
            select(GroupMembership.role).where(
                GroupMembership.org_id == actor.org_id,
                GroupMembership.group_id == project.owning_group_id,
                GroupMembership.user_id == actor.user_id,
            )
        ).scalar_one_or_none()
        if group_role == GroupRole.member:
            candidates.append(ProjectRole.contributor)
        if group_role == GroupRole.lead:
            candidates.append(ProjectRole.maintainer)
        explicit = self._projects_repository.get_membership(
            org_id=actor.org_id,
            project_id=project_id,
            user_id=actor.user_id,
        )
        if explicit is not None:
            candidates.append(explicit.role)
        if not candidates:
            return None
        return max(candidates, key=lambda role: PROJECT_ROLE_LEVELS[role])

    def can_create_memory(
        self,
        *,
        actor: ActorContext,
        visibility_scope: VisibilityScope,
        project_id: UUID | None,
        visibility_group_id: UUID | None,
    ) -> CreationDecision:
        self._validate_visibility_shape(
            visibility_scope=visibility_scope,
            project_id=project_id,
            visibility_group_id=visibility_group_id,
        )
        self._enforce_session_visibility_cap(actor, visibility_scope)
        membership = self.get_org_membership(actor)
        if membership is None:
            raise AuthorizationDeniedError()
        if visibility_scope in {VisibilityScope.private, VisibilityScope.restricted}:
            return CreationDecision(status=MemoryStatus.active, requires_review=False)
        if visibility_scope == VisibilityScope.group:
            group_role = self._group_role(actor=actor, group_id=_required_uuid(visibility_group_id))
            if group_role is None:
                raise AuthorizationDeniedError("The actor is not a member of the target group.")
            return CreationDecision(
                status=MemoryStatus.active
                if group_role == GroupRole.lead
                else MemoryStatus.pending_review,
                requires_review=group_role != GroupRole.lead,
            )
        if visibility_scope == VisibilityScope.project:
            role = self.get_effective_project_role(actor, _required_uuid(project_id))
            if role not in {ProjectRole.contributor, ProjectRole.reviewer, ProjectRole.maintainer}:
                raise AuthorizationDeniedError(
                    "The actor cannot create memory for the target project."
                )
            reviewer = role in {ProjectRole.reviewer, ProjectRole.maintainer}
            return CreationDecision(
                status=MemoryStatus.active if reviewer else MemoryStatus.pending_review,
                requires_review=not reviewer,
            )
        if membership.role == OrgRole.knowledge_admin:
            return CreationDecision(status=MemoryStatus.active, requires_review=False)
        return CreationDecision(status=MemoryStatus.pending_review, requires_review=True)

    def can_read_memory(
        self,
        *,
        actor: ActorContext,
        memory: MemoryEntry,
        statuses: tuple[MemoryStatus, ...] = DEFAULT_READ_STATUSES,
    ) -> bool:
        if (
            memory.org_id != actor.org_id
            or memory.deleted_at is not None
            or memory.status not in statuses
        ):
            return False
        return self._in_visibility_audience(actor=actor, memory=memory)

    def readable_memory_statement(
        self,
        actor: ActorContext,
        statuses: tuple[MemoryStatus, ...] = DEFAULT_READ_STATUSES,
    ) -> Select[tuple[MemoryEntry]]:
        return readable_memory_statement(self._db, actor=actor, statuses=statuses)

    def reviewable_memory_statement(
        self,
        actor: ActorContext,
        statuses: tuple[MemoryStatus, ...] = (MemoryStatus.pending_review,),
    ) -> Select[tuple[MemoryEntry]]:
        lead_group_ids = self._lead_group_ids(actor)
        review_project_ids = self._review_project_ids(actor)
        membership = self.get_org_membership(actor)
        review_conditions: list[ColumnElement[bool]] = []
        if lead_group_ids:
            review_conditions.append(
                and_(
                    MemoryEntry.visibility_scope == VisibilityScope.group,
                    MemoryEntry.visibility_group_id.in_(lead_group_ids),
                )
            )
        if review_project_ids:
            review_conditions.append(
                and_(
                    MemoryEntry.visibility_scope == VisibilityScope.project,
                    MemoryEntry.project_id.in_(review_project_ids),
                )
            )
        if membership is not None and membership.role == OrgRole.knowledge_admin:
            review_conditions.append(MemoryEntry.visibility_scope == VisibilityScope.organization)
        if not review_conditions:
            return select(MemoryEntry).where(false())
        return select(MemoryEntry).where(
            MemoryEntry.org_id == actor.org_id,
            MemoryEntry.deleted_at.is_(None),
            MemoryEntry.status.in_(list(statuses)),
            MemoryEntry.owner_user_id != actor.user_id,
            MemoryEntry.created_by_user_id != actor.user_id,
            or_(*review_conditions),
        )

    def can_review_memory(self, *, actor: ActorContext, memory: MemoryEntry) -> bool:
        if memory.status not in {MemoryStatus.pending_review, MemoryStatus.needs_review}:
            return False
        if memory.owner_user_id == actor.user_id or memory.created_by_user_id == actor.user_id:
            return False
        return self._controls_scope(actor=actor, memory=memory)

    def can_edit_memory(self, *, actor: ActorContext, memory: MemoryEntry) -> bool:
        if memory.deleted_at is not None or memory.org_id != actor.org_id:
            return False
        if memory.visibility_scope in {VisibilityScope.private, VisibilityScope.restricted}:
            return self._can_manage_private_or_restricted(actor=actor, memory=memory, edit=True)
        if memory.status == MemoryStatus.pending_review and memory.owner_user_id == actor.user_id:
            return True
        return memory.status in {
            MemoryStatus.active,
            MemoryStatus.needs_review,
        } and self._controls_scope(actor=actor, memory=memory)

    def can_manage_grants(self, *, actor: ActorContext, memory: MemoryEntry) -> bool:
        return (
            memory.visibility_scope == VisibilityScope.restricted
            and self._can_manage_private_or_restricted(
                actor=actor, memory=memory, edit=False, manage=True
            )
        )

    def can_archive_memory(self, *, actor: ActorContext, memory: MemoryEntry) -> bool:
        if memory.status not in {
            MemoryStatus.active,
            MemoryStatus.needs_review,
            MemoryStatus.deprecated,
        }:
            return False
        if memory.visibility_scope in {VisibilityScope.private, VisibilityScope.restricted}:
            return self._can_manage_private_or_restricted(
                actor=actor, memory=memory, edit=False, manage=True
            )
        return self._controls_scope(actor=actor, memory=memory)

    def can_soft_delete_memory(self, *, actor: ActorContext, memory: MemoryEntry) -> bool:
        if memory.visibility_scope in {VisibilityScope.private, VisibilityScope.restricted}:
            return self._can_manage_private_or_restricted(
                actor=actor, memory=memory, edit=False, manage=True
            )
        return (
            memory.status == MemoryStatus.pending_review and memory.owner_user_id == actor.user_id
        )

    def decide_visibility_change(
        self,
        *,
        actor: ActorContext,
        memory: MemoryEntry,
        target_scope: VisibilityScope,
        project_id: UUID | None,
        visibility_group_id: UUID | None,
    ) -> VisibilityDecision:
        if not self.can_edit_memory(actor=actor, memory=memory):
            raise AuthorizationDeniedError()
        self._validate_visibility_shape(
            visibility_scope=target_scope,
            project_id=project_id,
            visibility_group_id=visibility_group_id,
        )
        self._enforce_session_visibility_cap(actor, target_scope)
        if VISIBILITY_LEVELS[target_scope] <= VISIBILITY_LEVELS[memory.visibility_scope]:
            return VisibilityDecision(status=memory.status, requires_review=False)
        decision = self.can_create_memory(
            actor=actor,
            visibility_scope=target_scope,
            project_id=project_id,
            visibility_group_id=visibility_group_id,
        )
        return VisibilityDecision(status=decision.status, requires_review=decision.requires_review)

    def _in_visibility_audience(self, *, actor: ActorContext, memory: MemoryEntry) -> bool:
        if memory.owner_user_id == actor.user_id:
            return True
        if memory.visibility_scope == VisibilityScope.restricted:
            grant = self._grant(actor=actor, memory_id=memory.id)
            return grant is not None
        if (
            memory.visibility_scope == VisibilityScope.group
            and memory.visibility_group_id is not None
        ):
            return self._group_role(actor=actor, group_id=memory.visibility_group_id) is not None
        if memory.visibility_scope == VisibilityScope.project and memory.project_id is not None:
            return self.get_effective_project_role(actor, memory.project_id) is not None
        if memory.visibility_scope == VisibilityScope.organization:
            return self.get_org_membership(actor) is not None
        return False

    def _controls_scope(self, *, actor: ActorContext, memory: MemoryEntry) -> bool:
        if (
            memory.visibility_scope == VisibilityScope.group
            and memory.visibility_group_id is not None
        ):
            return (
                self._group_role(actor=actor, group_id=memory.visibility_group_id) == GroupRole.lead
            )
        if memory.visibility_scope == VisibilityScope.project and memory.project_id is not None:
            return self.get_effective_project_role(actor, memory.project_id) in {
                ProjectRole.reviewer,
                ProjectRole.maintainer,
            }
        if memory.visibility_scope == VisibilityScope.organization:
            membership = self.get_org_membership(actor)
            return membership is not None and membership.role == OrgRole.knowledge_admin
        return False

    def _can_manage_private_or_restricted(
        self,
        *,
        actor: ActorContext,
        memory: MemoryEntry,
        edit: bool,
        manage: bool = False,
    ) -> bool:
        if memory.owner_user_id == actor.user_id:
            return True
        if memory.visibility_scope != VisibilityScope.restricted:
            return False
        grant = self._grant(actor=actor, memory_id=memory.id)
        if grant is None:
            return False
        if manage:
            return grant.role == GrantRole.manager
        if edit:
            return grant.role in {GrantRole.editor, GrantRole.manager}
        return grant.role in {GrantRole.viewer, GrantRole.editor, GrantRole.manager}

    def _group_role(self, *, actor: ActorContext, group_id: UUID) -> GroupRole | None:
        return self._db.execute(
            select(GroupMembership.role).where(
                GroupMembership.org_id == actor.org_id,
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == actor.user_id,
            )
        ).scalar_one_or_none()

    def _lead_group_ids(self, actor: ActorContext) -> list[UUID]:
        return list(
            self._db.execute(
                select(GroupMembership.group_id).where(
                    GroupMembership.org_id == actor.org_id,
                    GroupMembership.user_id == actor.user_id,
                    GroupMembership.role == GroupRole.lead,
                )
            )
            .scalars()
            .all()
        )

    def _review_project_ids(self, actor: ActorContext) -> list[UUID]:
        projects = (
            self._db.execute(select(Project).where(Project.org_id == actor.org_id)).scalars().all()
        )
        return [
            project.id
            for project in projects
            if self.get_effective_project_role(actor, project.id)
            in {ProjectRole.reviewer, ProjectRole.maintainer}
        ]

    def _grant(self, *, actor: ActorContext, memory_id: UUID) -> MemoryEntryGrant | None:
        return self._db.execute(
            select(MemoryEntryGrant).where(
                MemoryEntryGrant.org_id == actor.org_id,
                MemoryEntryGrant.memory_entry_id == memory_id,
                MemoryEntryGrant.grantee_user_id == actor.user_id,
            )
        ).scalar_one_or_none()

    def _enforce_session_visibility_cap(
        self, actor: ActorContext, visibility_scope: VisibilityScope
    ) -> None:
        if actor.session_max_visibility_scope is None:
            return
        if (
            VISIBILITY_LEVELS[visibility_scope]
            > VISIBILITY_LEVELS[actor.session_max_visibility_scope]
        ):
            self._audit_service.record_denial(
                actor=actor,
                reason="session_visibility_cap",
                metadata={"visibility_scope": visibility_scope.value},
            )
            self._db.flush()
            raise AuthorizationDeniedError("The session cannot use the requested visibility scope.")

    def _validate_visibility_shape(
        self,
        *,
        visibility_scope: VisibilityScope,
        project_id: UUID | None,
        visibility_group_id: UUID | None,
    ) -> None:
        if visibility_scope == VisibilityScope.group and visibility_group_id is None:
            raise ValidationProblem("Group visibility requires visibility_group_id.")
        if visibility_scope != VisibilityScope.group and visibility_group_id is not None:
            raise ValidationProblem("Only group visibility may set visibility_group_id.")
        if visibility_scope == VisibilityScope.project and project_id is None:
            raise ValidationProblem("Project visibility requires project_id.")


def readable_memory_statement(
    db: Session,
    *,
    actor: ActorContext,
    statuses: tuple[MemoryStatus, ...] = DEFAULT_READ_STATUSES,
) -> Select[tuple[MemoryEntry]]:
    group_ids = list(
        db.execute(
            select(GroupMembership.group_id).where(
                GroupMembership.org_id == actor.org_id,
                GroupMembership.user_id == actor.user_id,
            )
        )
        .scalars()
        .all()
    )
    project_ids = list_effective_project_ids(db, actor=actor)
    grant_exists = exists().where(
        MemoryEntryGrant.org_id == MemoryEntry.org_id,
        MemoryEntryGrant.memory_entry_id == MemoryEntry.id,
        MemoryEntryGrant.grantee_user_id == actor.user_id,
        MemoryEntryGrant.role.in_([GrantRole.viewer, GrantRole.editor, GrantRole.manager]),
    )
    conditions = [
        MemoryEntry.owner_user_id == actor.user_id,
        and_(MemoryEntry.visibility_scope == VisibilityScope.restricted, grant_exists),
        MemoryEntry.visibility_scope == VisibilityScope.organization,
    ]
    if group_ids:
        conditions.append(
            and_(
                MemoryEntry.visibility_scope == VisibilityScope.group,
                MemoryEntry.visibility_group_id.in_(group_ids),
            )
        )
    if project_ids:
        conditions.append(
            and_(
                MemoryEntry.visibility_scope == VisibilityScope.project,
                MemoryEntry.project_id.in_(project_ids),
            )
        )
    return select(MemoryEntry).where(
        MemoryEntry.org_id == actor.org_id,
        MemoryEntry.deleted_at.is_(None),
        MemoryEntry.status.in_(list(statuses)),
        or_(*conditions),
    )


def list_effective_project_ids(db: Session, *, actor: ActorContext) -> list[UUID]:
    explicit = select(ProjectMembership.project_id).where(
        ProjectMembership.org_id == actor.org_id,
        ProjectMembership.user_id == actor.user_id,
    )
    inherited = (
        select(Project.id)
        .join(GroupMembership, GroupMembership.group_id == Project.owning_group_id)
        .where(GroupMembership.org_id == actor.org_id, GroupMembership.user_id == actor.user_id)
    )
    return list(db.execute(explicit.union(inherited)).scalars().all())


def _required_uuid(value: UUID | None) -> UUID:
    if value is None:
        raise ValidationProblem("Required identifier is missing.")
    return value
