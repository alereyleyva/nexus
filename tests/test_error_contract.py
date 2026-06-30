from __future__ import annotations

from typing import Protocol, cast

import httpx
from fastapi.testclient import TestClient

from app.main import create_app


class HttpClient(Protocol):
    def get(self, url: str) -> httpx.Response: ...

    def post(self, url: str, *, json: object) -> httpx.Response: ...


def test_healthcheck_returns_liveness_without_authentication() -> None:
    client = cast(HttpClient, TestClient(create_app()))
    response = client.get("/health")
    assert response.status_code == 200
    body = cast(dict[str, object], response.json())
    assert body["status"] == "ok"


def test_api_errors_use_common_problem_envelope() -> None:
    client = cast(HttpClient, TestClient(create_app()))
    response = client.post("/v1/auth/cli/authorizations", json={"client_name": ""})
    body = cast(dict[str, object], response.json())
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert body["code"] == "VALIDATION_FAILED"
    assert "request_id" in body


def test_missing_auth_uses_unauthenticated_problem_envelope() -> None:
    client = cast(HttpClient, TestClient(create_app()))
    response = client.get("/v1/memory-entries")
    assert response.status_code == 401
    body = cast(dict[str, object], response.json())
    assert body["code"] == "UNAUTHENTICATED"
