from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_session_capability
from app.modules.auth.types import ActorContext
from app.modules.search.schemas import SearchRequest, SearchResponse
from app.modules.search.service import SearchService

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_memory(
    request: SearchRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("search:read"))],
    db: Session = Depends(get_db_session),
) -> SearchResponse:
    return SearchService(db).search(actor=actor, request=request)
