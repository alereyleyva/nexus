from __future__ import annotations

import pytest

from nexus_cli.cli import main
from nexus_cli.client import ApiClient, ApiError
from tests.conftest import ScriptedTransport

_API = "http://localhost:8000"


def test_create_memory_sends_bearer_and_returns_body(transport: ScriptedTransport) -> None:
    transport.add("/v1/memory-entries", 201, {"id": "mem-1", "status": "active"})
    client = ApiClient(_API, transport=transport, access_token="acc-token")

    entry = client.create_memory({"type": "note", "title": "t", "body": "b"})

    assert entry["status"] == "active"
    call = transport.calls[-1]
    assert call.method == "POST"
    assert call.headers["Authorization"] == "Bearer acc-token"
    assert "X-Request-Id" in call.headers


def test_auth_call_without_token_raises_before_transport(transport: ScriptedTransport) -> None:
    client = ApiClient(_API, transport=transport)
    with pytest.raises(ApiError) as excinfo:
        client.me()
    assert excinfo.value.status == 401
    assert transport.calls == []


def test_error_response_is_mapped_to_api_error(transport: ScriptedTransport) -> None:
    transport.add(
        "/v1/memory-entries",
        422,
        {"code": "VALIDATION_FAILED", "detail": "title is required"},
    )
    client = ApiClient(_API, transport=transport, access_token="acc-token")

    with pytest.raises(ApiError) as excinfo:
        client.create_memory({"type": "note"})
    assert excinfo.value.status == 422
    assert excinfo.value.code == "VALIDATION_FAILED"


def test_main_without_command_returns_usage_code() -> None:
    assert main([]) == 2


def test_main_memory_without_subcommand_returns_usage_code() -> None:
    assert main(["memory"]) == 2
