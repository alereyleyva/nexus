from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import AuthorizationDeniedError, ConflictError, UnauthenticatedError
from app.config import Settings
from app.modules.auth.models import AuthClientType, AuthRefreshToken
from app.modules.auth.service import AuthService
from app.modules.authorization.service import AuthorizationService
from app.modules.memory_entries.models import VisibilityScope
from app.modules.memory_entries.service import MemoryEntryService
from tests.conftest import SeedData, actor, memory_request


def test_oidc_login_creates_session_and_actor_context_resolves(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    tokens = service.create_session_for_user(
        org_id=seed.org.id,
        user_id=seed.pablo.id,
        provider="google",
        provider_subject="google-pablo",
        client_type=AuthClientType.web,
        client_name="web",
        capabilities=[],
        max_visibility_scope=None,
    )
    actor_context = service.validate_access_token(token=tokens.access_token, request_id="req-auth")
    assert actor_context.user_id == seed.pablo.id
    assert actor_context.org_id == seed.org.id
    assert actor_context.session_id == tokens.session_id


def test_refresh_token_rotation_issues_new_credentials(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    tokens = service.create_session_for_user(
        org_id=seed.org.id,
        user_id=seed.pablo.id,
        provider="google",
        provider_subject="google-pablo",
        client_type=AuthClientType.cli,
        client_name="nexus-cli",
        capabilities=["memory:read"],
        max_visibility_scope=VisibilityScope.project,
    )
    refreshed = service.refresh_session(refresh_token=tokens.refresh_token)
    used_tokens = (
        db.execute(select(AuthRefreshToken).where(AuthRefreshToken.session_id == tokens.session_id))
        .scalars()
        .all()
    )
    assert refreshed.refresh_token != tokens.refresh_token
    assert any(token.used_at is not None for token in used_tokens)


def test_refresh_token_reuse_revokes_session(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    tokens = service.create_session_for_user(
        org_id=seed.org.id,
        user_id=seed.pablo.id,
        provider="google",
        provider_subject="google-pablo",
        client_type=AuthClientType.cli,
        client_name="nexus-cli",
        capabilities=[],
        max_visibility_scope=None,
    )
    service.refresh_session(refresh_token=tokens.refresh_token)
    with pytest.raises(UnauthenticatedError):
        service.refresh_session(refresh_token=tokens.refresh_token)


def test_session_capability_is_required_for_restricted_sessions(
    db: Session, seed: SeedData
) -> None:
    restricted_actor = actor(
        org_id=seed.org.id, user_id=seed.pablo.id, capabilities={"memory:read"}
    )
    with pytest.raises(AuthorizationDeniedError):
        AuthorizationService(db).require_capability(restricted_actor, "memory:create")


def test_session_cannot_create_above_max_visibility_scope(db: Session, seed: SeedData) -> None:
    restricted_actor = actor(
        org_id=seed.org.id,
        user_id=seed.pablo.id,
        capabilities={"memory:create"},
        max_visibility_scope=VisibilityScope.project,
    )
    with pytest.raises(AuthorizationDeniedError):
        MemoryEntryService(db).create_memory(
            actor=restricted_actor,
            request=memory_request(visibility_scope=VisibilityScope.organization),
        )


def test_cli_authorization_polls_then_exchanges_once(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    started = service.start_cli_authorization(
        client_name="nexus-cli",
        requested_capabilities=["memory:read"],
        max_visibility_scope=VisibilityScope.project,
    )
    pending = service.exchange_cli_token(device_code=started.device_code)
    assert pending == "authorization_pending"
    service.approve_cli_authorization_for_user(
        user_code=started.user_code, org_id=seed.org.id, user_id=seed.pablo.id
    )
    exchanged = service.exchange_cli_token(device_code=started.device_code)
    assert exchanged != "authorization_pending"
    with pytest.raises(ConflictError):
        service.exchange_cli_token(device_code=started.device_code)


def test_session_listing_and_revocation(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    tokens = service.create_session_for_user(
        org_id=seed.org.id,
        user_id=seed.pablo.id,
        provider="google",
        provider_subject="google-pablo",
        client_type=AuthClientType.web,
        client_name="web",
        capabilities=[],
        max_visibility_scope=None,
    )
    actor_context = service.validate_access_token(token=tokens.access_token, request_id="req-auth")
    assert len(service.list_sessions(actor=actor_context)) == 1
    service.revoke_session(actor=actor_context)
    with pytest.raises(UnauthenticatedError):
        service.validate_access_token(token=tokens.access_token, request_id="req-auth")


def test_invalid_access_token_is_rejected(db: Session) -> None:
    with pytest.raises(UnauthenticatedError):
        AuthService(db, settings=_settings()).validate_access_token(
            token="not-a-token",  # noqa: S106 - deliberately invalid test credential.
            request_id="req-auth",
        )


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        token_secret="test-token-secret-with-enough-length",  # noqa: S106 - deterministic test key.
    )
