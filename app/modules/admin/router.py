from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_session_capability
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
from app.modules.admin.service import AdminService
from app.modules.auth.types import ActorContext

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/users", response_model=UsersAdminResponse)
def list_users(
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> UsersAdminResponse:
    return AdminService(db).list_users(actor=actor)


@router.post("/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: CreateUserRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> UserAdminResponse:
    return AdminService(db).create_user(actor=actor, request=request)


@router.patch("/users/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> UserAdminResponse:
    return AdminService(db).update_user(actor=actor, user_id=user_id, request=request)


@router.put("/org-memberships/{user_id}", response_model=UserAdminResponse)
def set_org_membership(
    user_id: UUID,
    request: SetOrgMembershipRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> UserAdminResponse:
    return AdminService(db).set_org_membership(actor=actor, user_id=user_id, request=request)


@router.get("/groups", response_model=GroupsResponse)
def list_groups(
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> GroupsResponse:
    return AdminService(db).list_groups(actor=actor)


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    request: CreateGroupRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> GroupResponse:
    return AdminService(db).create_group(actor=actor, request=request)


@router.put("/groups/{group_id}/memberships/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def set_group_membership(
    group_id: UUID,
    user_id: UUID,
    request: SetGroupMembershipRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> None:
    AdminService(db).set_group_membership(
        actor=actor, group_id=group_id, user_id=user_id, request=request
    )


@router.get("/projects", response_model=ProjectsResponse)
def list_projects(
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> ProjectsResponse:
    return AdminService(db).list_projects(actor=actor)


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> ProjectResponse:
    return AdminService(db).create_project(actor=actor, request=request)


@router.put("/projects/{project_id}/memberships/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def set_project_membership(
    project_id: UUID,
    user_id: UUID,
    request: SetProjectMembershipRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("admin:manage"))],
    db: Session = Depends(get_db_session),
) -> None:
    AdminService(db).set_project_membership(
        actor=actor, project_id=project_id, user_id=user_id, request=request
    )
