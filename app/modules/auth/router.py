from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.dependencies import get_actor_context, get_db_session, require_session_capability
from app.modules.auth.models import AuthClientType
from app.modules.auth.schemas import (
    ActorContextResponse,
    AuthProviderResponse,
    AuthProvidersResponse,
    CliApprovalResponse,
    CliAuthorizationDetailsResponse,
    CliPendingResponse,
    CliTokenRequest,
    DevLoginRequest,
    RefreshSessionRequest,
    SessionResponse,
    SessionsResponse,
    StartCliAuthorizationRequest,
    StartCliAuthorizationResponse,
    TokenResponse,
    WebSessionRequest,
)
from app.modules.auth.service import AuthService
from app.modules.auth.types import ActorContext

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/providers", response_model=AuthProvidersResponse)
def list_providers(db: Session = Depends(get_db_session)) -> AuthProvidersResponse:
    service = AuthService(db)
    return AuthProvidersResponse(
        providers=[AuthProviderResponse(**provider) for provider in service.providers()]
    )


@router.post(
    "/cli/authorizations",
    response_model=StartCliAuthorizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_cli_authorization(
    request: StartCliAuthorizationRequest,
    db: Session = Depends(get_db_session),
) -> StartCliAuthorizationResponse:
    return AuthService(db).start_cli_authorization(
        client_name=request.client_name,
        requested_capabilities=request.requested_capabilities,
        max_visibility_scope=request.max_visibility_scope,
    )


@router.get(
    "/cli/authorizations/{user_code}",
    response_model=CliAuthorizationDetailsResponse,
)
def read_cli_authorization(
    user_code: str,
    db: Session = Depends(get_db_session),
) -> CliAuthorizationDetailsResponse:
    return AuthService(db).get_pending_cli_authorization(user_code=user_code)


@router.post(
    "/cli/authorizations/{user_code}/approve",
    response_model=CliApprovalResponse,
)
def approve_cli_authorization(
    user_code: str,
    actor: ActorContext = Depends(get_actor_context),
    db: Session = Depends(get_db_session),
) -> CliApprovalResponse:
    AuthService(db).approve_cli_authorization_for_user(user_code=user_code, actor=actor)
    return CliApprovalResponse(status="approved")


@router.post(
    "/cli/authorizations/{user_code}/deny",
    response_model=CliApprovalResponse,
)
def deny_cli_authorization(
    user_code: str,
    actor: ActorContext = Depends(get_actor_context),
    db: Session = Depends(get_db_session),
) -> CliApprovalResponse:
    AuthService(db).deny_cli_authorization_for_user(user_code=user_code, actor=actor)
    return CliApprovalResponse(status="denied")


@router.post("/cli/token", response_model=TokenResponse | CliPendingResponse)
def exchange_cli_token(
    request: CliTokenRequest,
    db: Session = Depends(get_db_session),
) -> TokenResponse | CliPendingResponse:
    result = AuthService(db).exchange_cli_token(device_code=request.device_code)
    if result == "authorization_pending":
        return CliPendingResponse(status="authorization_pending", interval=5)
    return result


@router.get("/oidc/{provider}/authorize")
def oidc_authorize(
    provider: str,
    redirect_uri: str = Query(min_length=1),
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    url = AuthService(db).build_oidc_authorization_url(provider=provider, redirect_uri=redirect_uri)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/oidc/{provider}/callback")
def oidc_callback(
    provider: str,
    code: str = Query(min_length=1),
    state: str = Query(min_length=1),
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    target = AuthService(db).complete_oidc_login(provider=provider, code=code, state=state)
    return RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)


@router.post("/web/dev-login", response_model=TokenResponse)
def dev_login(
    request: DevLoginRequest,
    db: Session = Depends(get_db_session),
) -> TokenResponse:
    return AuthService(db).dev_login(email=request.email)


@router.post("/web/session", response_model=TokenResponse)
def exchange_web_login(
    request: WebSessionRequest,
    db: Session = Depends(get_db_session),
) -> TokenResponse:
    return AuthService(db).exchange_web_login(login_code=request.login_code)


@router.post("/session/refresh", response_model=TokenResponse)
def refresh_session(
    request: RefreshSessionRequest,
    db: Session = Depends(get_db_session),
) -> TokenResponse:
    return AuthService(db).refresh_session(refresh_token=request.refresh_token)


@router.post("/session/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_current_session(
    actor: ActorContext = Depends(get_actor_context),
    db: Session = Depends(get_db_session),
) -> None:
    AuthService(db).revoke_session(actor=actor)


@router.get("/me", response_model=ActorContextResponse)
def read_me(
    actor: Annotated[ActorContext, Depends(require_session_capability("auth:read"))],
) -> ActorContextResponse:
    return ActorContextResponse(
        org_id=actor.org_id,
        user_id=actor.user_id,
        session_id=actor.session_id,
        capabilities=sorted(actor.session_capabilities),
        max_visibility_scope=actor.session_max_visibility_scope,
        client_type=AuthClientType(actor.client_type),
    )


@router.get("/sessions", response_model=SessionsResponse)
def list_sessions(
    actor: Annotated[ActorContext, Depends(require_session_capability("auth:sessions:manage"))],
    db: Session = Depends(get_db_session),
) -> SessionsResponse:
    return SessionsResponse(
        items=[
            SessionResponse.model_validate(session)
            for session in AuthService(db).list_sessions(actor=actor)
        ]
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(
    session_id: UUID,
    actor: Annotated[ActorContext, Depends(require_session_capability("auth:sessions:manage"))],
    db: Session = Depends(get_db_session),
) -> None:
    AuthService(db).revoke_session(actor=actor, session_id=session_id)
