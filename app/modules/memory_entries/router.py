from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_session_capability
from app.modules.auth.types import ActorContext
from app.modules.memory_entries.models import MemoryStatus
from app.modules.memory_entries.schemas import (
    AddGrantRequest,
    BulkCreateMemoryEntriesRequest,
    BulkCreateMemoryEntriesResponse,
    ChangeVisibilityRequest,
    CreateMemoryEntryRequest,
    GrantResponse,
    LifecycleReasonRequest,
    MemoryEntryListResponse,
    MemoryEntryResponse,
    MemoryMutationResponse,
    ReviewMemoryEntryRequest,
    UpdateMemoryEntryRequest,
)
from app.modules.memory_entries.service import MemoryEntryService

router = APIRouter(tags=["memory_entries"])


@router.get("/v1/memory-entries", response_model=MemoryEntryListResponse)
def list_memory_entries(
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:read"))],
    db: Session = Depends(get_db_session),
    project_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    status_filter: list[MemoryStatus] = Query(default=[], alias="status"),
) -> MemoryEntryListResponse:
    statuses = status_filter or None
    return MemoryEntryService(db).list_memory(
        actor=actor, project_id=project_id, limit=limit, statuses=statuses
    )


@router.post(
    "/v1/memory-entries",
    response_model=MemoryMutationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_memory_entry(
    request: CreateMemoryEntryRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:create"))],
    db: Session = Depends(get_db_session),
) -> MemoryMutationResponse:
    return MemoryEntryService(db).create_memory(actor=actor, request=request)


@router.post(
    "/v1/memory-entries:bulk",
    response_model=BulkCreateMemoryEntriesResponse,
    status_code=status.HTTP_201_CREATED,
)
def bulk_create_memory_entries(
    request: BulkCreateMemoryEntriesRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:create"))],
    db: Session = Depends(get_db_session),
) -> BulkCreateMemoryEntriesResponse:
    return MemoryEntryService(db).bulk_create_memory(actor=actor, request=request)


@router.get("/v1/memory-entries/{memory_id}", response_model=MemoryEntryResponse)
def get_memory_entry(
    memory_id: UUID,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:read"))],
    db: Session = Depends(get_db_session),
) -> MemoryEntryResponse:
    return MemoryEntryService(db).get_memory(actor=actor, memory_id=memory_id)


@router.patch("/v1/memory-entries/{memory_id}", response_model=MemoryEntryResponse)
def update_memory_entry(
    memory_id: UUID,
    request: UpdateMemoryEntryRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:update"))],
    db: Session = Depends(get_db_session),
) -> MemoryEntryResponse:
    return MemoryEntryService(db).update_memory(actor=actor, memory_id=memory_id, request=request)


@router.post("/v1/memory-entries/{memory_id}/review", response_model=MemoryMutationResponse)
def review_memory_entry(
    memory_id: UUID,
    request: ReviewMemoryEntryRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:review"))],
    db: Session = Depends(get_db_session),
) -> MemoryMutationResponse:
    return MemoryEntryService(db).review_memory(actor=actor, memory_id=memory_id, request=request)


@router.post(
    "/v1/memory-entries/{memory_id}/mark-needs-review", response_model=MemoryMutationResponse
)
def mark_memory_needs_review(
    memory_id: UUID,
    request: LifecycleReasonRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:review"))],
    db: Session = Depends(get_db_session),
) -> MemoryMutationResponse:
    return MemoryEntryService(db).mark_needs_review(
        actor=actor, memory_id=memory_id, reason=request.reason
    )


@router.post("/v1/memory-entries/{memory_id}/deprecate", response_model=MemoryMutationResponse)
def deprecate_memory_entry(
    memory_id: UUID,
    request: LifecycleReasonRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:review"))],
    db: Session = Depends(get_db_session),
) -> MemoryMutationResponse:
    return MemoryEntryService(db).deprecate_memory(
        actor=actor, memory_id=memory_id, reason=request.reason
    )


@router.post("/v1/memory-entries/{memory_id}/archive", response_model=MemoryMutationResponse)
def archive_memory_entry(
    memory_id: UUID,
    request: LifecycleReasonRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:update"))],
    db: Session = Depends(get_db_session),
) -> MemoryMutationResponse:
    return MemoryEntryService(db).archive_memory(
        actor=actor, memory_id=memory_id, reason=request.reason
    )


@router.delete("/v1/memory-entries/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory_entry(
    memory_id: UUID,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:update"))],
    db: Session = Depends(get_db_session),
) -> None:
    MemoryEntryService(db).soft_delete_memory(actor=actor, memory_id=memory_id)


@router.patch("/v1/memory-entries/{memory_id}/visibility", response_model=MemoryMutationResponse)
def change_memory_visibility(
    memory_id: UUID,
    request: ChangeVisibilityRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:update"))],
    db: Session = Depends(get_db_session),
) -> MemoryMutationResponse:
    return MemoryEntryService(db).change_visibility(
        actor=actor, memory_id=memory_id, request=request
    )


@router.post("/v1/memory-entries/{memory_id}/grants", response_model=GrantResponse)
def add_memory_grant(
    memory_id: UUID,
    request: AddGrantRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("grants:manage"))],
    db: Session = Depends(get_db_session),
) -> GrantResponse:
    return MemoryEntryService(db).add_grant(actor=actor, memory_id=memory_id, request=request)


@router.delete(
    "/v1/memory-entries/{memory_id}/grants/{grant_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_memory_grant(
    memory_id: UUID,
    grant_id: UUID,
    actor: Annotated[ActorContext, Depends(require_session_capability("grants:manage"))],
    db: Session = Depends(get_db_session),
) -> None:
    MemoryEntryService(db).delete_grant(actor=actor, memory_id=memory_id, grant_id=grant_id)


@router.get("/v1/review-queue", response_model=MemoryEntryListResponse)
def review_queue(
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:review"))],
    db: Session = Depends(get_db_session),
    limit: int = Query(default=50, ge=1, le=100),
) -> MemoryEntryListResponse:
    return MemoryEntryService(db).review_queue(actor=actor, limit=limit)
