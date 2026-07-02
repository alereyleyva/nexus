from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.common.errors import NotFoundError, UnauthenticatedError
from app.config import Settings
from app.modules.auth.service import AuthService
from app.modules.identity.models import UserStatus
from tests.conftest import SeedData


@pytest.mark.usefixtures("seed")
def test_dev_login_is_disabled_by_default(db: Session) -> None:
    service = AuthService(db, settings=_settings(dev_login_enabled=False))
    with pytest.raises(NotFoundError):
        service.dev_login(email="morgan@example.com")


def test_dev_login_issues_web_session_for_active_user(db: Session, seed: SeedData) -> None:
    service = AuthService(db, settings=_settings(dev_login_enabled=True))
    tokens = service.dev_login(email="morgan@example.com")
    actor_context = service.validate_access_token(token=tokens.access_token, request_id="req-dev")
    assert actor_context.user_id == seed.morgan.id
    assert actor_context.org_id == seed.org.id
    assert tokens.capabilities == []


@pytest.mark.usefixtures("seed")
def test_dev_login_rejects_unknown_email(db: Session) -> None:
    service = AuthService(db, settings=_settings(dev_login_enabled=True))
    with pytest.raises(UnauthenticatedError):
        service.dev_login(email="nobody@example.com")


def test_dev_login_rejects_disabled_user(db: Session, seed: SeedData) -> None:
    seed.dana.status = UserStatus.disabled
    db.commit()
    service = AuthService(db, settings=_settings(dev_login_enabled=True))
    with pytest.raises(UnauthenticatedError):
        service.dev_login(email="dana@example.com")


def _settings(*, dev_login_enabled: bool) -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        token_secret="test-token-secret-with-enough-length",  # noqa: S106 - deterministic test key.
        dev_login_enabled=dev_login_enabled,
        dev_login_org_slug="acme",
    )
