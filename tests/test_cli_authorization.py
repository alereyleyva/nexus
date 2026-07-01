from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from app.common.errors import BadRequestError, ConflictError, NotFoundError, UnauthenticatedError
from app.common.time import utc_now
from app.config import Settings
from app.modules.auth.models import AuthCliAuthorization, CliAuthorizationStatus
from app.modules.auth.service import AuthService
from app.modules.memory_entries.models import VisibilityScope
from tests.conftest import SeedData, actor


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        token_secret="test-token-secret-with-enough-length",  # noqa: S106 - deterministic test key.
        web_base_url="https://app.nexus.test",
    )


def _start(service: AuthService) -> tuple[str, str]:
    response = service.start_cli_authorization(
        client_name="nexus-cli",
        requested_capabilities=["memory:create", "memory:read"],
        max_visibility_scope=VisibilityScope.project,
    )
    assert response.verification_uri.startswith("https://app.nexus.test/cli/approve?code=")
    return response.device_code, response.user_code


def test_verification_uri_points_at_web_client(db: Session) -> None:
    service = AuthService(db, settings=_settings())
    _, user_code = _start(service)
    details = service.get_pending_cli_authorization(user_code=user_code)
    assert details.client_name == "nexus-cli"
    assert details.requested_capabilities == ["memory:create", "memory:read"]
    assert details.max_visibility_scope == VisibilityScope.project
    assert details.status == "pending"
    assert details.expires_in > 0


def test_read_unknown_user_code_is_not_found(db: Session) -> None:
    service = AuthService(db, settings=_settings())
    with pytest.raises(NotFoundError):
        service.get_pending_cli_authorization(user_code="ABCD-EFGH")


def test_approve_binds_user_and_allows_token_exchange(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    device_code, user_code = _start(service)
    approver = actor(org_id=seed.org.id, user_id=seed.pablo.id)

    authorization = service.approve_cli_authorization_for_user(user_code=user_code, actor=approver)

    assert authorization.status == CliAuthorizationStatus.approved
    assert authorization.org_id == seed.org.id
    assert authorization.user_id == seed.pablo.id

    tokens = service.exchange_cli_token(device_code=device_code)
    assert not isinstance(tokens, str)
    resolved = service.validate_access_token(token=tokens.access_token, request_id="req")
    assert resolved.user_id == seed.pablo.id
    assert resolved.session_capabilities == {"memory:create", "memory:read"}
    assert resolved.session_max_visibility_scope == VisibilityScope.project


def test_deny_blocks_token_exchange(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    device_code, user_code = _start(service)
    denier = actor(org_id=seed.org.id, user_id=seed.pablo.id)

    authorization = service.deny_cli_authorization_for_user(user_code=user_code, actor=denier)
    assert authorization.status == CliAuthorizationStatus.denied

    with pytest.raises(UnauthenticatedError):
        service.exchange_cli_token(device_code=device_code)


def test_approve_twice_conflicts(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    _, user_code = _start(service)
    approver = actor(org_id=seed.org.id, user_id=seed.pablo.id)

    service.approve_cli_authorization_for_user(user_code=user_code, actor=approver)
    with pytest.raises(ConflictError):
        service.approve_cli_authorization_for_user(user_code=user_code, actor=approver)


def test_expired_authorization_cannot_be_approved(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings())
    _, user_code = _start(service)
    stored = db.query(AuthCliAuthorization).one()
    stored.expires_at = utc_now() - timedelta(seconds=1)
    db.commit()
    approver = actor(org_id=seed.org.id, user_id=seed.pablo.id)

    with pytest.raises(BadRequestError):
        service.approve_cli_authorization_for_user(user_code=user_code, actor=approver)
    with pytest.raises(NotFoundError):
        service.get_pending_cli_authorization(user_code=user_code)
