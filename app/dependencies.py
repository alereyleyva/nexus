from __future__ import annotations

from collections.abc import Callable, Generator
from uuid import uuid4

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.common.errors import UnauthenticatedError
from app.db.session import get_session
from app.modules.auth.service import AuthService
from app.modules.auth.types import ActorContext
from app.modules.authorization.service import AuthorizationService


def get_db_session() -> Generator[Session]:
    yield from get_session()


def get_request_id(request: Request, x_request_id: str | None = Header(default=None)) -> str:
    request_id = x_request_id or str(uuid4())
    request.state.request_id = request_id
    return request_id


def get_actor_context(
    request_id: str = Depends(get_request_id),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db_session),
) -> ActorContext:
    if authorization is None or not authorization.startswith("Bearer "):
        raise UnauthenticatedError()
    token = authorization.removeprefix("Bearer ").strip()
    return AuthService(db).validate_access_token(token=token, request_id=request_id)


def require_session_capability(capability: str) -> Callable[[ActorContext, Session], ActorContext]:
    def dependency(
        actor: ActorContext = Depends(get_actor_context),
        db: Session = Depends(get_db_session),
    ) -> ActorContext:
        AuthorizationService(db).require_capability(actor, capability)
        return actor

    return dependency
