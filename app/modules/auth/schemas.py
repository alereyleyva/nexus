from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.models import AuthClientType
from app.modules.memory_entries.models import VisibilityScope


class AuthProviderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    type: str


class AuthProvidersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: list[AuthProviderResponse]


class StartCliAuthorizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_name: str = Field(min_length=1, max_length=100)
    requested_capabilities: list[str] = Field(default_factory=list)
    max_visibility_scope: VisibilityScope | None = None


class StartCliAuthorizationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class CliTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_code: str


class CliPendingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    interval: int


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "Bearer"  # noqa: S105 - OAuth token type literal, not a password.
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    session_id: UUID
    org_id: UUID
    user_id: UUID
    capabilities: list[str]
    max_visibility_scope: VisibilityScope | None


class RefreshSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class DevLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3)


class ActorContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    org_id: UUID
    user_id: UUID
    session_id: UUID
    capabilities: list[str]
    max_visibility_scope: VisibilityScope | None
    client_type: AuthClientType


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_type: AuthClientType
    client_name: str | None
    capabilities: list[str]
    max_visibility_scope: VisibilityScope | None
    expires_at: datetime
    revoked_at: datetime | None
    last_used_at: datetime | None


class SessionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SessionResponse]
