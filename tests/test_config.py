from __future__ import annotations

from typing import Any

import boto3
import pytest

from app import config


def _clear() -> None:
    config.get_settings.cache_clear()


def test_plain_env_value_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_OIDC_ORG_SLUG", "custom-org")
    _clear()
    try:
        assert config.get_settings().oidc_org_slug == "custom-org"
    finally:
        _clear()


def test_missing_env_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEXUS_OIDC_ORG_SLUG", raising=False)
    _clear()
    try:
        assert config.get_settings().oidc_org_slug == "aircury"
    finally:
        _clear()


def test_ssm_pointer_is_resolved_at_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake_resolve(name: str) -> str:
        seen.append(name)
        return "r" * 32

    monkeypatch.setattr(config, "_resolve_ssm_parameter", fake_resolve)
    monkeypatch.setenv("NEXUS_TOKEN_SECRET", "ssm:/nexus/prod/token-secret")
    _clear()
    try:
        assert config.get_settings().token_secret == "r" * 32
        assert seen == ["/nexus/prod/token-secret"]
    finally:
        _clear()


def test_ssm_pointer_supported_for_list_values(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_resolve(_name: str) -> str:
        return "https://a.example,https://b.example"

    monkeypatch.setattr(config, "_resolve_ssm_parameter", fake_resolve)
    monkeypatch.setenv("NEXUS_CORS_ORIGINS", "ssm:/nexus/prod/cors")
    _clear()
    try:
        assert config.get_settings().cors_allow_origins == (
            "https://a.example",
            "https://b.example",
        )
    finally:
        _clear()


def test_resolver_reads_decrypted_ssm_value(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_client(service: str) -> Any:
        assert service == "ssm"

        class _Client:
            def get_parameter(self, **kwargs: Any) -> dict[str, Any]:
                assert kwargs["WithDecryption"] is True
                return {"Parameter": {"Name": kwargs["Name"], "Value": "x" * 32}}

        return _Client()

    monkeypatch.setattr(boto3, "client", fake_client)
    monkeypatch.setenv("NEXUS_TOKEN_SECRET", "ssm:/nexus/prod/token-secret")
    _clear()
    try:
        assert config.get_settings().token_secret == "x" * 32
    finally:
        _clear()


def test_resolver_rejects_non_string(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_client(_service: str) -> Any:
        class _Client:
            def get_parameter(self, **_kwargs: Any) -> dict[str, Any]:
                return {"Parameter": {"Value": 123}}

        return _Client()

    monkeypatch.setattr(boto3, "client", fake_client)
    monkeypatch.setenv("NEXUS_TOKEN_SECRET", "ssm:/nexus/prod/token-secret")
    _clear()
    try:
        with pytest.raises(TypeError):
            config.get_settings()
    finally:
        _clear()
