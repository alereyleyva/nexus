from __future__ import annotations

from pathlib import Path

import pytest

from nexus_cli.auth import LoginError, authenticate, login
from nexus_cli.credentials import Credentials, load_credentials, save_credentials
from tests.conftest import ScriptedTransport

_API = "http://localhost:8000"

_TOKENS = {
    "access_token": "acc-token",
    "token_type": "Bearer",
    "expires_in": 900,
    "refresh_token": "nxs_rt_new",
    "refresh_expires_in": 43200,
    "session_id": "11111111-1111-4111-8111-111111111111",
    "org_id": "22222222-2222-4222-8222-222222222222",
    "user_id": "33333333-3333-4333-8333-333333333333",
}


def test_login_polls_until_approved(transport: ScriptedTransport, creds_file: Path) -> None:
    _ = creds_file
    transport.add(
        "/v1/auth/cli/authorizations",
        201,
        {
            "device_code": "dev-code",
            "user_code": "ABCD-EFGH",
            "verification_uri": "http://web/cli/approve?code=ABCD-EFGH",
            "expires_in": 600,
            "interval": 5,
        },
    )
    transport.add("/v1/auth/cli/token", 200, {"status": "authorization_pending", "interval": 5})
    transport.add("/v1/auth/cli/token", 200, _TOKENS)
    opened: list[str] = []

    credentials = login(
        _API,
        transport=transport,
        open_url=lambda url: bool(opened.append(url)) or True,
        sleep=lambda _seconds: None,
        printer=lambda _line: None,
    )

    assert credentials.refresh_token == "nxs_rt_new"
    assert credentials.user_id == _TOKENS["user_id"]
    assert opened == ["http://web/cli/approve?code=ABCD-EFGH"]


def test_login_times_out_when_never_approved(
    transport: ScriptedTransport, creds_file: Path
) -> None:
    _ = creds_file
    transport.add(
        "/v1/auth/cli/authorizations",
        201,
        {
            "device_code": "dev-code",
            "user_code": "ABCD-EFGH",
            "verification_uri": "http://web/cli/approve?code=ABCD-EFGH",
            "expires_in": 5,
            "interval": 5,
        },
    )
    for _ in range(3):
        transport.add("/v1/auth/cli/token", 200, {"status": "authorization_pending", "interval": 5})

    with pytest.raises(LoginError):
        login(
            _API,
            transport=transport,
            open_url=lambda _url: True,
            sleep=lambda _seconds: None,
            printer=lambda _line: None,
        )


def test_authenticate_rotates_and_persists_refresh_token(
    transport: ScriptedTransport, creds_file: Path
) -> None:
    _ = creds_file
    save_credentials(
        Credentials(
            api_url=_API,
            refresh_token="nxs_rt_old",
            session_id=str(_TOKENS["session_id"]),
            org_id=str(_TOKENS["org_id"]),
            user_id=str(_TOKENS["user_id"]),
        )
    )
    transport.add("/v1/auth/session/refresh", 200, _TOKENS)

    client, rotated = authenticate(load_credentials_or_fail(), transport=transport)

    assert rotated.refresh_token == "nxs_rt_new"
    assert load_credentials_or_fail().refresh_token == "nxs_rt_new"
    # The returned client carries the fresh access token for subsequent calls.
    transport.add("/v1/auth/me", 200, {"user_id": _TOKENS["user_id"]})
    assert client.me()["user_id"] == _TOKENS["user_id"]


def test_authenticate_maps_expired_session_to_login_error(
    transport: ScriptedTransport, creds_file: Path
) -> None:
    _ = creds_file
    credentials = Credentials(
        api_url=_API,
        refresh_token="nxs_rt_old",
        session_id=str(_TOKENS["session_id"]),
        org_id=str(_TOKENS["org_id"]),
        user_id=str(_TOKENS["user_id"]),
    )
    transport.add(
        "/v1/auth/session/refresh",
        401,
        {"code": "UNAUTHENTICATED", "detail": "Invalid refresh token."},
    )

    with pytest.raises(LoginError):
        authenticate(credentials, transport=transport)


def load_credentials_or_fail() -> Credentials:
    credentials = load_credentials()
    assert credentials is not None
    return credentials
