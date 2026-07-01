from __future__ import annotations

import time
import webbrowser
from collections.abc import Callable, Mapping
from dataclasses import replace

from nexus_cli.client import ApiClient, ApiError
from nexus_cli.config import DEFAULT_CAPABILITIES
from nexus_cli.credentials import Credentials, save_credentials
from nexus_cli.http import Transport


class LoginError(Exception):
    """Raised when a browser login cannot be completed."""


def login(
    api_url: str,
    *,
    transport: Transport | None = None,
    open_url: Callable[[str], bool] = webbrowser.open,
    sleep: Callable[[float], None] = time.sleep,
    printer: Callable[[str], None] = print,
) -> Credentials:
    client = ApiClient(api_url, transport=transport)
    started = client.start_cli_authorization(
        client_name="nexus-cli",
        requested_capabilities=DEFAULT_CAPABILITIES,
        max_visibility_scope=None,
    )
    device_code = _require_str(started, "device_code")
    verification_uri = _require_str(started, "verification_uri")
    interval = _require_int(started, "interval", default=5)
    expires_in = _require_int(started, "expires_in", default=600)

    printer("Open this URL in your browser to approve the login:")
    printer(f"  {verification_uri}")
    open_url(verification_uri)

    deadline = expires_in
    waited = 0
    while waited <= deadline:
        result = client.poll_cli_token(device_code=device_code)
        if result.get("status") != "authorization_pending":
            return _credentials_from_tokens(api_url, result)
        sleep(interval)
        waited += interval
    raise LoginError("The login request expired before it was approved.")


def authenticate(
    credentials: Credentials, *, transport: Transport | None = None
) -> tuple[ApiClient, Credentials]:
    """Refresh the session, persist the rotated refresh token, and return an authed client."""
    base = ApiClient(credentials.api_url, transport=transport)
    try:
        tokens = base.refresh_session(refresh_token=credentials.refresh_token)
    except ApiError as error:
        if error.status == 401:
            raise LoginError("Your session expired. Run 'nexus login' again.") from error
        raise
    rotated = replace(
        credentials,
        refresh_token=_require_str(tokens, "refresh_token"),
        session_id=_require_str(tokens, "session_id"),
    )
    save_credentials(rotated)
    return base.with_token(_require_str(tokens, "access_token")), rotated


def _credentials_from_tokens(api_url: str, tokens: Mapping[str, object]) -> Credentials:
    return Credentials(
        api_url=api_url,
        refresh_token=_require_str(tokens, "refresh_token"),
        session_id=_require_str(tokens, "session_id"),
        org_id=_require_str(tokens, "org_id"),
        user_id=_require_str(tokens, "user_id"),
    )


def _require_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise LoginError(f"The API response is missing '{key}'.")
    return value


def _require_int(mapping: Mapping[str, object], key: str, *, default: int) -> int:
    value = mapping.get(key)
    return value if isinstance(value, int) else default
