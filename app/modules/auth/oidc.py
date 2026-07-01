from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Protocol, cast

_GOOGLE_AUTHORIZATION_ENDPOINT: Final = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_ENDPOINT: Final = "https://oauth2.googleapis.com/token"  # noqa: S105 - public URL.
_GOOGLE_ISSUERS: Final = frozenset({"https://accounts.google.com", "accounts.google.com"})
_HTTP_TIMEOUT_SECONDS: Final = 10


class OidcError(Exception):
    """Raised when an OIDC provider exchange or identity claim check fails."""


@dataclass(frozen=True)
class OidcIdentity:
    email: str
    subject: str
    email_verified: bool


class OidcProvider(Protocol):
    def build_authorization_url(self, *, redirect_uri: str, state: str, nonce: str) -> str: ...

    def exchange_code(self, *, code: str, redirect_uri: str, nonce: str) -> OidcIdentity: ...


class GoogleOidcProvider:
    def __init__(self, *, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def build_authorization_url(self, *, redirect_uri: str, state: str, nonce: str) -> str:
        query = urllib.parse.urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email",
                "state": state,
                "nonce": nonce,
                "access_type": "online",
                "prompt": "select_account",
            }
        )
        return f"{_GOOGLE_AUTHORIZATION_ENDPOINT}?{query}"

    def exchange_code(self, *, code: str, redirect_uri: str, nonce: str) -> OidcIdentity:
        claims = self._claims_from_id_token(
            self._request_id_token(code=code, redirect_uri=redirect_uri)
        )
        _require(claims.get("iss") in _GOOGLE_ISSUERS, "Unexpected token issuer.")
        _require(claims.get("aud") == self._client_id, "Unexpected token audience.")
        _require(claims.get("nonce") == nonce, "Nonce mismatch.")
        email = claims.get("email")
        _require(isinstance(email, str) and bool(email), "Missing email claim.")
        subject = claims.get("sub")
        _require(isinstance(subject, str) and bool(subject), "Missing subject claim.")
        return OidcIdentity(
            email=cast(str, email),
            subject=cast(str, subject),
            email_verified=claims.get("email_verified") is True,
        )

    def _request_id_token(self, *, code: str, redirect_uri: str) -> str:
        payload = urllib.parse.urlencode(
            {
                "code": code,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        ).encode()
        request = urllib.request.Request(  # noqa: S310 - fixed https provider endpoint.
            _GOOGLE_TOKEN_ENDPOINT,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                body = cast(Mapping[str, object], json.loads(response.read().decode()))
        except (urllib.error.URLError, ValueError, json.JSONDecodeError) as error:
            raise OidcError("The provider token exchange failed.") from error
        id_token = body.get("id_token")
        if not isinstance(id_token, str) or not id_token:
            raise OidcError("The provider did not return an id_token.")
        return id_token

    def _claims_from_id_token(self, id_token: str) -> Mapping[str, object]:
        parts = id_token.split(".")
        if len(parts) != 3:
            raise OidcError("Malformed id_token.")
        try:
            padded = f"{parts[1]}{'=' * (-len(parts[1]) % 4)}"
            decoded = json.loads(base64.urlsafe_b64decode(padded).decode())
        except (ValueError, json.JSONDecodeError) as error:
            raise OidcError("Unreadable id_token payload.") from error
        if not isinstance(decoded, dict):
            raise OidcError("Unexpected id_token payload.")
        return cast(Mapping[str, object], decoded)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OidcError(message)


def build_google_provider(*, client_id: str, client_secret: str) -> GoogleOidcProvider:
    return GoogleOidcProvider(client_id=client_id, client_secret=client_secret)
