from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.ids import new_uuid
from app.common.time import utc_now
from app.db.base import Base
from app.db.types import STRING_LIST
from app.modules.memory_entries.models import VisibilityScope


class AuthClientType(StrEnum):
    web = "web"
    cli = "cli"
    future_integration = "future_integration"


class CliAuthorizationStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    expired = "expired"
    exchanged = "exchanged"


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_subject: Mapped[str] = mapped_column(String, nullable=False)
    client_type: Mapped[AuthClientType] = mapped_column(
        Enum(AuthClientType, name="auth_client_type", native_enum=False), nullable=False
    )
    client_name: Mapped[str | None] = mapped_column(String, nullable=True)
    capabilities: Mapped[list[str]] = mapped_column(STRING_LIST, default=list)
    max_visibility_scope: Mapped[VisibilityScope | None] = mapped_column(
        Enum(VisibilityScope, name="visibility_scope", native_enum=False), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("auth_sessions_org_id_unique", "org_id", "id", unique=True),
        Index("auth_sessions_user_idx", "org_id", "user_id"),
        Index("auth_sessions_provider_subject_idx", "org_id", "provider", "provider_subject"),
        Index("auth_sessions_lifecycle_idx", "org_id", "revoked_at", "expires_at"),
    )


class AuthCliAuthorization(Base):
    __tablename__ = "auth_cli_authorizations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    device_code_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    user_code_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[CliAuthorizationStatus] = mapped_column(
        Enum(CliAuthorizationStatus, name="cli_authorization_status", native_enum=False),
        nullable=False,
    )
    requested_capabilities: Mapped[list[str]] = mapped_column(STRING_LIST, default=list)
    max_visibility_scope: Mapped[VisibilityScope | None] = mapped_column(
        Enum(VisibilityScope, name="cli_max_visibility_scope", native_enum=False), nullable=True
    )
    client_name: Mapped[str] = mapped_column(String, nullable=False)
    approved_session_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exchanged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("auth_cli_authorizations_device_code_hash_unique", "device_code_hash", unique=True),
        Index("auth_cli_authorizations_user_code_hash_unique", "user_code_hash", unique=True),
        Index("auth_cli_authorizations_status_expires_idx", "status", "expires_at"),
        Index("auth_cli_authorizations_user_idx", "org_id", "user_id"),
    )


class AuthWebLogin(Base):
    __tablename__ = "auth_web_logins"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("auth_sessions.id"))
    login_code_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("auth_web_logins_login_code_hash_unique", "login_code_hash", unique=True),
        Index("auth_web_logins_session_idx", "org_id", "session_id"),
    )


class AuthRefreshToken(Base):
    __tablename__ = "auth_refresh_tokens"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id"))
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("auth_sessions.id"))
    token_hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    parent_token_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("auth_refresh_tokens_token_hash_unique", "token_hash", unique=True),
        Index("auth_refresh_tokens_session_idx", "org_id", "session_id"),
    )
