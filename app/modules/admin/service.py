from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.errors import AuthorizationDeniedError, ConflictError, NotFoundError
from app.common.time import utc_now
from app.modules.admin.schemas import (
    CreateGroupRequest,
    CreateProjectRequest,
    CreateUserRequest,
    GroupResponse,
    GroupsResponse,
    ProjectResponse,
    ProjectsResponse,
    SetGroupMembershipRequest,
    SetOrgMembershipRequest,
    SetProjectMembershipRequest,
    UpdateUserRequest,
    UserAdminResponse,
    UsersAdminResponse,
)
from app.modules.audit.models import AuditDecision
from app.modules.audit.service import AuditService
from app.modules.auth.types import ActorContext
from app.modules.authorization.service import AuthorizationService
from app.modules.groups.models import Group, GroupMembership
from app.modules.groups.repository import GroupsRepository
from app.modules.identity.models import OrgMembership, User
from app.modules.identity.repository import IdentityRepository
from app.modules.projects.models import Project, ProjectMembership
from app.modules.projects.repository import ProjectsRepository


class AdminService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._identity_repository = IdentityRepository(db)
        self._groups_repository = GroupsRepository(db)
        self._projects_repository = ProjectsRepository(db)
        self._authorization = AuthorizationService(db)
        self._audit_service = AuditService(db)

    def create_user(self, *, actor: ActorContext, request: CreateUserRequest) -> UserAdminResponse:
        self._require_admin(actor)
        existing = self._identity_repository.get_user_by_email_for_org(
            org_id=actor.org_id, email=request.email
        )
        if existing is not None:
            raise ConflictError("A user with this email already exists.")
        user = User(
            org_id=actor.org_id,
            email=request.email,
            display_name=request.display_name,
            status=request.status,
        )
        self._identity_repository.add_user(user)
        self._db.flush()
        membership = OrgMembership(
            org_id=actor.org_id,
            user_id=user.id,
            role=request.role,
            is_org_admin=request.is_org_admin,
        )
        self._identity_repository.add_org_membership(membership)
        self._audit_service.record_event(
            actor=actor,
            action="admin.user_changed",
            resource_type="user",
            resource_id=user.id,
            decision=AuditDecision.allow,
            metadata={"target_user_id": str(user.id)},
        )
        self._db.commit()
        return _user_response(user, membership)

    def list_users(self, *, actor: ActorContext) -> UsersAdminResponse:
        self._require_admin(actor)
        users = self._identity_repository.list_users_for_org(org_id=actor.org_id)
        return UsersAdminResponse(
            items=[self._response_for_user(actor.org_id, user) for user in users]
        )

    def update_user(
        self, *, actor: ActorContext, user_id: UUID, request: UpdateUserRequest
    ) -> UserAdminResponse:
        self._require_admin(actor)
        user = self._identity_repository.get_user_by_id_for_org(
            org_id=actor.org_id, user_id=user_id
        )
        if user is None:
            raise NotFoundError("user")
        if request.display_name is not None:
            user.display_name = request.display_name
        if request.status is not None:
            user.status = request.status
        user.updated_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="admin.user_changed",
            resource_type="user",
            resource_id=user.id,
            decision=AuditDecision.allow,
            metadata={"target_user_id": str(user.id)},
        )
        self._db.commit()
        return self._response_for_user(actor.org_id, user)

    def set_org_membership(
        self, *, actor: ActorContext, user_id: UUID, request: SetOrgMembershipRequest
    ) -> UserAdminResponse:
        self._require_admin(actor)
        membership = self._identity_repository.get_membership(org_id=actor.org_id, user_id=user_id)
        user = self._identity_repository.get_user_by_id_for_org(
            org_id=actor.org_id, user_id=user_id
        )
        if membership is None or user is None:
            raise NotFoundError("organization membership")
        if membership.is_org_admin and not request.is_org_admin:
            admin_count = self._identity_repository.count_org_admins(org_id=actor.org_id)
            if admin_count <= 1:
                raise ConflictError("The last organization admin cannot be removed.")
            if actor.user_id == user_id:
                raise ConflictError("The actor cannot remove their last administrative access.")
        role_before = membership.role
        admin_before = membership.is_org_admin
        membership.role = request.role
        membership.is_org_admin = request.is_org_admin
        membership.updated_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="admin.org_membership_changed",
            resource_type="org_membership",
            resource_id=membership.id,
            decision=AuditDecision.allow,
            metadata={
                "target_user_id": str(user_id),
                "role_before": role_before.value,
                "role_after": membership.role.value,
                "is_org_admin_before": admin_before,
                "is_org_admin_after": membership.is_org_admin,
            },
        )
        self._db.commit()
        return _user_response(user, membership)

    def create_group(self, *, actor: ActorContext, request: CreateGroupRequest) -> GroupResponse:
        self._require_admin(actor)
        group = Group(
            org_id=actor.org_id,
            slug=request.slug,
            name=request.name,
            group_type=request.group_type,
            parent_group_id=request.parent_group_id,
        )
        self._groups_repository.add_group(group)
        self._db.flush()
        self._audit_service.record_event(
            actor=actor,
            action="admin.group_changed",
            resource_type="group",
            resource_id=group.id,
            decision=AuditDecision.allow,
            metadata={"group_id": str(group.id)},
        )
        self._db.commit()
        return GroupResponse.model_validate(group)

    def list_groups(self, *, actor: ActorContext) -> GroupsResponse:
        self._require_admin(actor)
        return GroupsResponse(
            items=[
                GroupResponse.model_validate(group)
                for group in self._groups_repository.list_groups(org_id=actor.org_id)
            ]
        )

    def set_group_membership(
        self,
        *,
        actor: ActorContext,
        group_id: UUID,
        user_id: UUID,
        request: SetGroupMembershipRequest,
    ) -> None:
        self._require_admin(actor)
        membership = self._groups_repository.get_membership(
            org_id=actor.org_id, group_id=group_id, user_id=user_id
        )
        if membership is None:
            membership = GroupMembership(
                org_id=actor.org_id, group_id=group_id, user_id=user_id, role=request.role
            )
            self._groups_repository.add_membership(membership)
        else:
            membership.role = request.role
        self._audit_service.record_event(
            actor=actor,
            action="admin.group_membership_changed",
            resource_type="group",
            resource_id=group_id,
            decision=AuditDecision.allow,
            metadata={"group_id": str(group_id), "target_user_id": str(user_id)},
        )
        self._db.commit()

    def create_project(
        self, *, actor: ActorContext, request: CreateProjectRequest
    ) -> ProjectResponse:
        self._require_admin(actor)
        project = Project(
            org_id=actor.org_id,
            owning_group_id=request.owning_group_id,
            key=request.key,
            name=request.name,
            description=request.description,
            status=request.status,
        )
        self._projects_repository.add_project(project)
        self._db.flush()
        self._audit_service.record_event(
            actor=actor,
            action="admin.project_changed",
            resource_type="project",
            resource_id=project.id,
            decision=AuditDecision.allow,
            metadata={"project_id": str(project.id)},
        )
        self._db.commit()
        return ProjectResponse.model_validate(project)

    def list_projects(self, *, actor: ActorContext) -> ProjectsResponse:
        self._require_admin(actor)
        return ProjectsResponse(
            items=[
                ProjectResponse.model_validate(project)
                for project in self._projects_repository.list_projects(org_id=actor.org_id)
            ]
        )

    def set_project_membership(
        self,
        *,
        actor: ActorContext,
        project_id: UUID,
        user_id: UUID,
        request: SetProjectMembershipRequest,
    ) -> None:
        self._require_admin(actor)
        membership = self._projects_repository.get_membership(
            org_id=actor.org_id, project_id=project_id, user_id=user_id
        )
        if membership is None:
            membership = ProjectMembership(
                org_id=actor.org_id, project_id=project_id, user_id=user_id, role=request.role
            )
            self._projects_repository.add_membership(membership)
        else:
            membership.role = request.role
        self._audit_service.record_event(
            actor=actor,
            action="admin.project_membership_changed",
            resource_type="project",
            resource_id=project_id,
            decision=AuditDecision.allow,
            metadata={"project_id": str(project_id), "target_user_id": str(user_id)},
        )
        self._db.commit()

    def _require_admin(self, actor: ActorContext) -> None:
        if not self._authorization.can_administer_organization(actor):
            self._audit_service.record_denial(actor=actor, reason="not_owner_or_manager")
            self._db.commit()
            raise AuthorizationDeniedError("Organization admin capability is required.")

    def _response_for_user(self, org_id: UUID, user: User) -> UserAdminResponse:
        membership = self._identity_repository.get_membership(org_id=org_id, user_id=user.id)
        if membership is None:
            raise NotFoundError("organization membership")
        return _user_response(user, membership)


def _user_response(user: User, membership: OrgMembership) -> UserAdminResponse:
    return UserAdminResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        status=user.status,
        role=membership.role,
        is_org_admin=membership.is_org_admin,
    )
