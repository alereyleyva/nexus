from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_session_capability
from app.modules.auth.types import ActorContext
from app.modules.projects.schemas import ProjectTimelineResponse
from app.modules.projects.service import ProjectService

router = APIRouter(prefix="/v1/projects", tags=["projects"])


@router.get("/{project_id}/timeline", response_model=ProjectTimelineResponse)
def project_timeline(
    project_id: UUID,
    actor: Annotated[ActorContext, Depends(require_session_capability("memory:read"))],
    db: Session = Depends(get_db_session),
    limit: int = Query(default=50, ge=1, le=100),
) -> ProjectTimelineResponse:
    return ProjectService(db).timeline(actor=actor, project_id=project_id, limit=limit)
