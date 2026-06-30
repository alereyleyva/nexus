from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_session_capability
from app.modules.auth.types import ActorContext
from app.modules.context_packs.schemas import ContextPackRequest, ContextPackResponse
from app.modules.context_packs.service import ContextPackService

router = APIRouter(prefix="/v1/context-packs", tags=["context_packs"])


@router.post("", response_model=ContextPackResponse)
def generate_context_pack(
    request: ContextPackRequest,
    actor: Annotated[ActorContext, Depends(require_session_capability("context_pack:generate"))],
    db: Session = Depends(get_db_session),
) -> ContextPackResponse:
    return ContextPackService(db).generate(actor=actor, request=request)
