from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

# Env var values starting with this prefix are pointers to SSM Parameter Store
# parameters resolved (and decrypted) at runtime, e.g. `ssm:/nexus/prod/token-secret`.
# This keeps secret values out of the Lambda definition and env vars (ADR-0013).
SSM_PREFIX = "ssm:"

_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_local_env_file() -> None:
    """Populate os.environ from a repo-root .env file for local development.

    Real environment variables always win (we never overwrite an existing key),
    so this is a no-op in production, where secrets come from the platform / SSM
    and no .env file is deployed.
    """
    try:
        content = _DOTENV_PATH.read_text(encoding="utf-8")
    except OSError:
        return
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


_load_local_env_file()


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: str = "nexus-api"
    version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://nexus:nexus_dev_password@localhost:5433/nexus"
    token_secret: str = Field(default="dev-only-nexus-token-secret-change-me", min_length=24)
    token_issuer: str = "nexus-api"  # noqa: S105 - JWT issuer identifier, not a password.
    token_audience: str = "nexus-api"  # noqa: S105 - JWT audience identifier, not a password.
    access_token_seconds: int = 900
    refresh_token_seconds: int = 43_200
    session_seconds: int = 43_200
    cli_authorization_seconds: int = 600
    public_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:5173"
    dev_login_enabled: bool = False
    dev_login_org_slug: str = "acme"
    # Google OIDC production login. Empty client id/secret means OIDC is not configured.
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_org_slug: str = "acme"
    oidc_state_seconds: int = 600
    web_login_seconds: int = 300
    web_login_redirect_uris: tuple[str, ...] = ("http://localhost:5173/auth/callback",)
    # Frontend and API deploy separately; the web client calls the API cross-origin.
    cors_allow_origins: tuple[str, ...] = ("http://localhost:5173",)


def _resolve_ssm_parameter(name: str) -> str:
    """Fetch and decrypt an SSM Parameter Store value at runtime."""
    import boto3  # Imported lazily: only needed when an `ssm:` value is present.

    client = cast("Any", boto3).client("ssm")
    parameter = cast("dict[str, Any]", client.get_parameter(Name=name, WithDecryption=True))
    value = parameter["Parameter"]["Value"]
    if not isinstance(value, str):
        raise TypeError(f"SSM parameter {name!r} did not return a string value.")
    return value


def _getenv(name: str) -> str | None:
    """Read an env var, resolving an `ssm:<parameter>` value from SSM Parameter Store."""
    raw = os.getenv(name)
    if raw is None:
        return None
    if raw.startswith(SSM_PREFIX):
        return _resolve_ssm_parameter(raw.removeprefix(SSM_PREFIX))
    return raw


def _env(name: str, default: str) -> str:
    value = _getenv(name)
    return default if value is None else value


def _env_flag(name: str, default: bool) -> bool:
    raw = _getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_origins(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = _getenv(name)
    if raw is None:
        return default
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=_env("DATABASE_URL", Settings.model_fields["database_url"].default),
        token_secret=_env("NEXUS_TOKEN_SECRET", Settings.model_fields["token_secret"].default),
        public_base_url=_env(
            "NEXUS_PUBLIC_BASE_URL", Settings.model_fields["public_base_url"].default
        ),
        web_base_url=_env("NEXUS_WEB_BASE_URL", Settings.model_fields["web_base_url"].default),
        dev_login_enabled=_env_flag("NEXUS_DEV_LOGIN", False),
        dev_login_org_slug=_env(
            "NEXUS_DEV_LOGIN_ORG_SLUG", Settings.model_fields["dev_login_org_slug"].default
        ),
        oidc_client_id=_env("NEXUS_OIDC_CLIENT_ID", ""),
        oidc_client_secret=_env("NEXUS_OIDC_CLIENT_SECRET", ""),
        oidc_org_slug=_env("NEXUS_OIDC_ORG_SLUG", Settings.model_fields["oidc_org_slug"].default),
        web_login_redirect_uris=_env_origins(
            "NEXUS_WEB_LOGIN_REDIRECT_URIS",
            Settings.model_fields["web_login_redirect_uris"].default,
        ),
        cors_allow_origins=_env_origins(
            "NEXUS_CORS_ORIGINS", Settings.model_fields["cors_allow_origins"].default
        ),
    )
