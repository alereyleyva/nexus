from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_name: str = "nexus-api"
    version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://nexus:nexus_dev_password@localhost:5432/nexus"
    token_secret: str = Field(default="dev-only-nexus-token-secret-change-me", min_length=24)
    token_issuer: str = "nexus-api"  # noqa: S105 - JWT issuer identifier, not a password.
    token_audience: str = "nexus-api"  # noqa: S105 - JWT audience identifier, not a password.
    access_token_seconds: int = 900
    refresh_token_seconds: int = 43_200
    session_seconds: int = 43_200
    cli_authorization_seconds: int = 600
    public_base_url: str = "http://localhost:8000"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", Settings.model_fields["database_url"].default),
        token_secret=os.getenv("NEXUS_TOKEN_SECRET", Settings.model_fields["token_secret"].default),
        public_base_url=os.getenv(
            "NEXUS_PUBLIC_BASE_URL", Settings.model_fields["public_base_url"].default
        ),
    )
