from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import cast

from nexus_cli.http import Response, Transport, urllib_transport


class ApiError(Exception):
    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(f"{status} {code}: {detail}")
        self.status = status
        self.code = code
        self.detail = detail


class ApiClient:
    def __init__(
        self,
        api_url: str,
        *,
        transport: Transport | None = None,
        access_token: str | None = None,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._transport = transport if transport is not None else urllib_transport
        self._access_token = access_token

    def with_token(self, access_token: str) -> ApiClient:
        return ApiClient(self._api_url, transport=self._transport, access_token=access_token)

    def start_cli_authorization(
        self,
        *,
        client_name: str,
        requested_capabilities: list[str],
        max_visibility_scope: str | None,
    ) -> Mapping[str, object]:
        return self._request(
            "POST",
            "/v1/auth/cli/authorizations",
            json_body={
                "client_name": client_name,
                "requested_capabilities": requested_capabilities,
                "max_visibility_scope": max_visibility_scope,
            },
        )

    def poll_cli_token(self, *, device_code: str) -> Mapping[str, object]:
        return self._request("POST", "/v1/auth/cli/token", json_body={"device_code": device_code})

    def refresh_session(self, *, refresh_token: str) -> Mapping[str, object]:
        return self._request(
            "POST", "/v1/auth/session/refresh", json_body={"refresh_token": refresh_token}
        )

    def revoke_session(self) -> None:
        self._request("POST", "/v1/auth/session/revoke", auth=True, allow_empty=True)

    def me(self) -> Mapping[str, object]:
        return self._request("GET", "/v1/auth/me", auth=True)

    def create_memory(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        return self._request("POST", "/v1/memory-entries", json_body=payload, auth=True)

    def search(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        return self._request("POST", "/v1/search", json_body=payload, auth=True)

    def context_pack(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        return self._request("POST", "/v1/context-packs", json_body=payload, auth=True)

    def list_projects(self) -> Mapping[str, object]:
        return self._request("GET", "/v1/projects?limit=100", auth=True)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: object | None = None,
        auth: bool = False,
        allow_empty: bool = False,
    ) -> Mapping[str, object]:
        headers: dict[str, str] = {"X-Request-Id": str(uuid.uuid4())}
        if auth:
            if self._access_token is None:
                raise ApiError(401, "UNAUTHENTICATED", "Run 'nexus login' first.")
            headers["Authorization"] = f"Bearer {self._access_token}"
        response = self._transport(method, f"{self._api_url}{path}", headers, json_body)
        if response.status >= 400:
            raise _api_error(response)
        if allow_empty and response.body is None:
            return {}
        if not isinstance(response.body, Mapping):
            raise ApiError(response.status, "BAD_RESPONSE", "The API returned an unexpected body.")
        return cast(Mapping[str, object], response.body)


def _api_error(response: Response) -> ApiError:
    code = "ERROR"
    detail = "The request failed."
    if isinstance(response.body, Mapping):
        body = cast(Mapping[str, object], response.body)
        raw_code = body.get("code")
        raw_detail = body.get("detail") or body.get("title")
        if isinstance(raw_code, str):
            code = raw_code
        if isinstance(raw_detail, str):
            detail = raw_detail
    return ApiError(response.status, code, detail)
