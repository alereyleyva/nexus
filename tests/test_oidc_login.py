from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy.orm import Session

from app.common.errors import BadRequestError, NotFoundError, UnauthenticatedError
from app.config import Settings
from app.modules.auth.oidc import GoogleOidcProvider, OidcError, OidcIdentity
from app.modules.auth.service import AuthService
from app.modules.identity.models import UserStatus
from tests.conftest import SeedData

_REDIRECT = "https://app.nexus.test/auth/callback"


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        token_secret="test-token-secret-with-enough-length",  # noqa: S106 - deterministic test key.
        oidc_org_slug="acme",
        web_login_redirect_uris=(_REDIRECT,),
    )


class FakeOidcProvider:
    def __init__(self, identity: OidcIdentity | Exception) -> None:
        self._identity = identity
        self.last_state = ""
        self.last_nonce = ""

    def build_authorization_url(self, *, redirect_uri: str, state: str, nonce: str) -> str:
        self.last_state = state
        self.last_nonce = nonce
        return f"https://accounts.google.test/o/oauth2/v2/auth?redirect_uri={redirect_uri}&state={state}"

    def exchange_code(self, *, code: str, redirect_uri: str, nonce: str) -> OidcIdentity:  # noqa: ARG002
        if isinstance(self._identity, Exception):
            raise self._identity
        return self._identity


def _authorize(service: AuthService, provider: FakeOidcProvider) -> str:
    service.build_oidc_authorization_url(provider="google", redirect_uri=_REDIRECT)
    return provider.last_state


def _login_code(target: str) -> str | None:
    query = parse_qs(urlparse(target).query)
    codes = query.get("login_code")
    return codes[0] if codes else None


def test_authorize_rejects_unknown_provider(db: Session) -> None:
    service = AuthService(db, settings=_settings(), oidc_provider=FakeOidcProvider(_identity()))
    with pytest.raises(NotFoundError):
        service.build_oidc_authorization_url(provider="github", redirect_uri=_REDIRECT)


def test_authorize_rejects_unlisted_redirect(db: Session) -> None:
    service = AuthService(db, settings=_settings(), oidc_provider=FakeOidcProvider(_identity()))
    with pytest.raises(BadRequestError):
        service.build_oidc_authorization_url(
            provider="google", redirect_uri="https://evil.test/callback"
        )


def test_authorize_is_not_found_when_oidc_unconfigured(db: Session) -> None:
    service = AuthService(db, settings=_settings())
    with pytest.raises(NotFoundError):
        service.build_oidc_authorization_url(provider="google", redirect_uri=_REDIRECT)


def test_web_login_happy_path(db: Session, seed: SeedData) -> None:
    provider = FakeOidcProvider(_identity(email="morgan@example.com"))
    service = AuthService(db, settings=_settings(), oidc_provider=provider)
    state = _authorize(service, provider)

    target = service.complete_oidc_login(provider="google", code="auth-code", state=state)
    login_code = _login_code(target)
    assert login_code is not None
    assert target.startswith(_REDIRECT)

    tokens = service.exchange_web_login(login_code=login_code)
    resolved = service.validate_access_token(token=tokens.access_token, request_id="req")
    assert resolved.user_id == seed.morgan.id
    assert resolved.org_id == seed.org.id
    assert resolved.session_capabilities == set()


@pytest.mark.usefixtures("seed")
def test_login_code_is_single_use(db: Session) -> None:
    provider = FakeOidcProvider(_identity(email="morgan@example.com"))
    service = AuthService(db, settings=_settings(), oidc_provider=provider)
    state = _authorize(service, provider)
    target = service.complete_oidc_login(provider="google", code="auth-code", state=state)
    login_code = _login_code(target)
    assert login_code is not None

    service.exchange_web_login(login_code=login_code)
    with pytest.raises(UnauthenticatedError):
        service.exchange_web_login(login_code=login_code)


def test_unverified_email_is_rejected_without_session(db: Session) -> None:
    provider = FakeOidcProvider(_identity(email="morgan@example.com", email_verified=False))
    service = AuthService(db, settings=_settings(), oidc_provider=provider)
    state = _authorize(service, provider)
    target = service.complete_oidc_login(provider="google", code="auth-code", state=state)
    assert "error=email_not_verified" in target
    assert _login_code(target) is None


@pytest.mark.usefixtures("seed")
def test_unknown_user_is_rejected(db: Session) -> None:
    provider = FakeOidcProvider(_identity(email="stranger@example.com"))
    service = AuthService(db, settings=_settings(), oidc_provider=provider)
    state = _authorize(service, provider)
    target = service.complete_oidc_login(provider="google", code="auth-code", state=state)
    assert "error=user_not_authorized" in target


def test_disabled_user_is_rejected(db: Session, seed: SeedData) -> None:
    seed.dana.status = UserStatus.disabled
    db.commit()
    provider = FakeOidcProvider(_identity(email="dana@example.com"))
    service = AuthService(db, settings=_settings(), oidc_provider=provider)
    state = _authorize(service, provider)
    target = service.complete_oidc_login(provider="google", code="auth-code", state=state)
    assert "error=user_not_authorized" in target


def test_tampered_state_is_bad_request(db: Session) -> None:
    provider = FakeOidcProvider(_identity())
    service = AuthService(db, settings=_settings(), oidc_provider=provider)
    with pytest.raises(BadRequestError):
        service.complete_oidc_login(provider="google", code="auth-code", state="not-a-valid-state")


def test_provider_exchange_failure_redirects_with_error(db: Session) -> None:
    provider = FakeOidcProvider(OidcError("boom"))
    service = AuthService(db, settings=_settings(), oidc_provider=provider)
    state = _authorize(service, provider)
    target = service.complete_oidc_login(provider="google", code="auth-code", state=state)
    assert "error=oidc_exchange_failed" in target


def test_google_provider_validates_claims() -> None:
    provider = GoogleOidcProvider(client_id="client-123", client_secret="secret")  # noqa: S106
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "client-123",
        "sub": "google-subject",
        "email": "morgan@example.com",
        "email_verified": True,
        "nonce": "nonce-abc",
    }
    _stub_token_request(provider, claims)
    identity = provider.exchange_code(code="c", redirect_uri="r", nonce="nonce-abc")
    assert identity == OidcIdentity(
        email="morgan@example.com", subject="google-subject", email_verified=True
    )


@pytest.mark.parametrize(
    "override",
    [{"aud": "someone-else"}, {"iss": "https://evil.test"}, {"nonce": "wrong"}],
)
def test_google_provider_rejects_bad_claims(override: dict[str, object]) -> None:
    provider = GoogleOidcProvider(client_id="client-123", client_secret="secret")  # noqa: S106
    claims: dict[str, object] = {
        "iss": "https://accounts.google.com",
        "aud": "client-123",
        "sub": "google-subject",
        "email": "morgan@example.com",
        "email_verified": True,
        "nonce": "nonce-abc",
    }
    claims.update(override)
    _stub_token_request(provider, claims)
    with pytest.raises(OidcError):
        provider.exchange_code(code="c", redirect_uri="r", nonce="nonce-abc")


def _stub_token_request(provider: GoogleOidcProvider, claims: Mapping[str, object]) -> None:
    token = _id_token(claims)

    def _request(*, code: str, redirect_uri: str) -> str:  # noqa: ARG001 - stub ignores inputs.
        return token

    provider._request_id_token = _request  # type: ignore[method-assign]


def _identity(*, email: str = "morgan@example.com", email_verified: bool = True) -> OidcIdentity:
    return OidcIdentity(email=email, subject="google-subject", email_verified=email_verified)


def _id_token(payload: Mapping[str, object]) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"header.{body}.signature"
