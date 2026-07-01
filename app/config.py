from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field


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
    dev_login_org_slug: str = "aircury"
    # Google OIDC production login. Empty client id/secret means OIDC is not configured.
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_org_slug: str = "aircury"
    oidc_state_seconds: int = 600
    web_login_seconds: int = 300
    web_login_redirect_uris: tuple[str, ...] = ("http://localhost:5173/auth/callback",)
    # Frontend and API deploy separately; the web client calls the API cross-origin.
    cors_allow_origins: tuple[str, ...] = ("http://localhost:5173",)


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_origins(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None:
        return default
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", Settings.model_fields["database_url"].default),
        token_secret=os.getenv("NEXUS_TOKEN_SECRET", Settings.model_fields["token_secret"].default),
        public_base_url=os.getenv(
            "NEXUS_PUBLIC_BASE_URL", Settings.model_fields["public_base_url"].default
        ),
        web_base_url=os.getenv("NEXUS_WEB_BASE_URL", Settings.model_fields["web_base_url"].default),
        dev_login_enabled=_env_flag("NEXUS_DEV_LOGIN", False),
        dev_login_org_slug=os.getenv(
            "NEXUS_DEV_LOGIN_ORG_SLUG", Settings.model_fields["dev_login_org_slug"].default
        ),
        oidc_client_id=os.getenv("NEXUS_OIDC_CLIENT_ID", ""),
        oidc_client_secret=os.getenv("NEXUS_OIDC_CLIENT_SECRET", ""),
        oidc_org_slug=os.getenv(
            "NEXUS_OIDC_ORG_SLUG", Settings.model_fields["oidc_org_slug"].default
        ),
        web_login_redirect_uris=_env_origins(
            "NEXUS_WEB_LOGIN_REDIRECT_URIS",
            Settings.model_fields["web_login_redirect_uris"].default,
        ),
        cors_allow_origins=_env_origins(
            "NEXUS_CORS_ORIGINS", Settings.model_fields["cors_allow_origins"].default
        ),
    )
