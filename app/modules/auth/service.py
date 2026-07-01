from __future__ import annotations

import urllib.parse
from datetime import timedelta
from typing import Literal
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.errors import BadRequestError, ConflictError, NotFoundError, UnauthenticatedError
from app.common.json import JsonObject, JsonValue
from app.common.security import (
    decode_access_token,
    encode_access_token,
    generate_token,
    hash_secret,
)
from app.common.time import as_utc, utc_now
from app.config import Settings, get_settings
from app.modules.audit.models import AuditDecision
from app.modules.audit.service import AuditService
from app.modules.auth.models import (
    AuthCliAuthorization,
    AuthClientType,
    AuthRefreshToken,
    AuthSession,
    AuthWebLogin,
    CliAuthorizationStatus,
)
from app.modules.auth.oidc import OidcError, OidcProvider, build_google_provider
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    CliAuthorizationDetailsResponse,
    StartCliAuthorizationResponse,
    TokenResponse,
)
from app.modules.auth.types import ActorContext
from app.modules.identity.models import UserStatus
from app.modules.identity.repository import IdentityRepository
from app.modules.memory_entries.models import VisibilityScope

_OIDC_STATE_AUDIENCE = "nexus-oidc-state"


class AuthService:
    def __init__(
        self,
        db: Session,
        settings: Settings | None = None,
        *,
        oidc_provider: OidcProvider | None = None,
    ) -> None:
        self._db = db
        self._settings = settings if settings is not None else get_settings()
        self._repository = AuthRepository(db)
        self._identity_repository = IdentityRepository(db)
        self._audit_service = AuditService(db)
        self._oidc_provider = oidc_provider

    def providers(self) -> list[dict[str, str]]:
        return [{"id": "google", "label": "Google", "type": "oidc"}]

    def start_cli_authorization(
        self,
        *,
        client_name: str,
        requested_capabilities: list[str],
        max_visibility_scope: VisibilityScope | None,
    ) -> StartCliAuthorizationResponse:
        device_code = generate_token("dev", bytes_count=24)
        user_code = generate_token("usr", bytes_count=8).replace("_", "-").upper()
        expires_at = utc_now() + timedelta(seconds=self._settings.cli_authorization_seconds)
        authorization = AuthCliAuthorization(
            device_code_hash=hash_secret(device_code, self._settings.token_secret),
            user_code_hash=hash_secret(user_code, self._settings.token_secret),
            status=CliAuthorizationStatus.pending,
            requested_capabilities=requested_capabilities,
            max_visibility_scope=max_visibility_scope,
            client_name=client_name,
            expires_at=expires_at,
        )
        self._repository.add_cli_authorization(authorization)
        self._db.commit()
        return StartCliAuthorizationResponse(
            device_code=device_code,
            user_code=user_code,
            verification_uri=f"{self._settings.web_base_url}/cli/approve?code={user_code}",
            expires_in=self._settings.cli_authorization_seconds,
            interval=5,
        )

    def get_pending_cli_authorization(self, *, user_code: str) -> CliAuthorizationDetailsResponse:
        authorization = self._load_pending_cli_authorization_for_read(user_code=user_code)
        remaining = int((as_utc(authorization.expires_at) - utc_now()).total_seconds())
        return CliAuthorizationDetailsResponse(
            client_name=authorization.client_name,
            requested_capabilities=authorization.requested_capabilities,
            max_visibility_scope=authorization.max_visibility_scope,
            status=authorization.status.value,
            expires_in=max(remaining, 0),
        )

    def approve_cli_authorization_for_user(
        self, *, user_code: str, actor: ActorContext
    ) -> AuthCliAuthorization:
        authorization = self._load_pending_cli_authorization_for_decision(user_code=user_code)
        authorization.org_id = actor.org_id
        authorization.user_id = actor.user_id
        authorization.status = CliAuthorizationStatus.approved
        authorization.approved_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="auth.cli_authorization.approved",
            resource_type="auth_cli_authorization",
            resource_id=authorization.id,
            decision=AuditDecision.allow,
            metadata={"client_name": authorization.client_name},
        )
        self._db.commit()
        return authorization

    def deny_cli_authorization_for_user(
        self, *, user_code: str, actor: ActorContext
    ) -> AuthCliAuthorization:
        authorization = self._load_pending_cli_authorization_for_decision(user_code=user_code)
        authorization.status = CliAuthorizationStatus.denied
        self._audit_service.record_event(
            actor=actor,
            action="auth.cli_authorization.denied",
            resource_type="auth_cli_authorization",
            resource_id=authorization.id,
            decision=AuditDecision.deny,
            reason="cli_authorization_denied",
            metadata={"client_name": authorization.client_name},
        )
        self._db.commit()
        return authorization

    def _load_pending_cli_authorization_for_read(self, *, user_code: str) -> AuthCliAuthorization:
        authorization = self._repository.get_cli_authorization_by_user_hash(
            hash_secret(user_code, self._settings.token_secret)
        )
        if authorization is None:
            raise NotFoundError("CLI authorization")
        if as_utc(authorization.expires_at) <= utc_now():
            if authorization.status == CliAuthorizationStatus.pending:
                authorization.status = CliAuthorizationStatus.expired
                self._db.commit()
            raise NotFoundError("CLI authorization")
        return authorization

    def _load_pending_cli_authorization_for_decision(
        self, *, user_code: str
    ) -> AuthCliAuthorization:
        authorization = self._repository.get_cli_authorization_by_user_hash(
            hash_secret(user_code, self._settings.token_secret)
        )
        if authorization is None:
            raise NotFoundError("CLI authorization")
        if as_utc(authorization.expires_at) <= utc_now():
            authorization.status = CliAuthorizationStatus.expired
            self._db.commit()
            raise BadRequestError("The CLI authorization expired.")
        if authorization.status != CliAuthorizationStatus.pending:
            raise ConflictError("The CLI authorization cannot be updated in its current state.")
        return authorization

    def exchange_cli_token(
        self, *, device_code: str
    ) -> TokenResponse | Literal["authorization_pending"]:
        authorization = self._repository.get_cli_authorization_by_device_hash(
            hash_secret(device_code, self._settings.token_secret)
        )
        if authorization is None:
            raise BadRequestError("Invalid device code.")
        if as_utc(authorization.expires_at) <= utc_now():
            authorization.status = CliAuthorizationStatus.expired
            self._db.commit()
            raise BadRequestError("The CLI authorization expired.")
        if authorization.status == CliAuthorizationStatus.pending:
            return "authorization_pending"
        if authorization.status == CliAuthorizationStatus.denied:
            raise UnauthenticatedError("The CLI authorization was denied.")
        if authorization.status == CliAuthorizationStatus.exchanged:
            raise ConflictError("The device code was already exchanged.")
        if authorization.org_id is None or authorization.user_id is None:
            raise BadRequestError("The CLI authorization is incomplete.")
        token_response = self.create_session_for_user(
            org_id=authorization.org_id,
            user_id=authorization.user_id,
            provider="google",
            provider_subject=str(authorization.user_id),
            client_type=AuthClientType.cli,
            client_name=authorization.client_name,
            capabilities=authorization.requested_capabilities,
            max_visibility_scope=authorization.max_visibility_scope,
        )
        authorization.status = CliAuthorizationStatus.exchanged
        authorization.exchanged_at = utc_now()
        authorization.approved_session_id = token_response.session_id
        self._db.commit()
        return token_response

    def dev_login(self, *, email: str) -> TokenResponse:
        if not self._settings.dev_login_enabled:
            raise NotFoundError("resource")
        user = self._identity_repository.get_user_by_email_for_org(
            org_id=self._resolve_dev_org_id(), email=email
        )
        if user is None or user.status != UserStatus.active:
            raise UnauthenticatedError("The user cannot authenticate.")
        return self.create_session_for_user(
            org_id=user.org_id,
            user_id=user.id,
            provider="dev",
            provider_subject=str(user.id),
            client_type=AuthClientType.web,
            client_name="nexus-web",
            capabilities=[],
            max_visibility_scope=None,
        )

    def _resolve_dev_org_id(self) -> UUID:
        organization = self._identity_repository.get_organization_by_slug(
            self._settings.dev_login_org_slug
        )
        if organization is None:
            raise NotFoundError("organization")
        return organization.id

    def create_session_for_user(
        self,
        *,
        org_id: UUID,
        user_id: UUID,
        provider: str,
        provider_subject: str,
        client_type: AuthClientType,
        client_name: str | None,
        capabilities: list[str],
        max_visibility_scope: VisibilityScope | None,
    ) -> TokenResponse:
        session = self._start_session(
            org_id=org_id,
            user_id=user_id,
            provider=provider,
            provider_subject=provider_subject,
            client_type=client_type,
            client_name=client_name,
            capabilities=capabilities,
            max_visibility_scope=max_visibility_scope,
        )
        token_response = self._issue_token_pair(session=session, parent_token_id=None)
        self._db.commit()
        return token_response

    def _start_session(
        self,
        *,
        org_id: UUID,
        user_id: UUID,
        provider: str,
        provider_subject: str,
        client_type: AuthClientType,
        client_name: str | None,
        capabilities: list[str],
        max_visibility_scope: VisibilityScope | None,
    ) -> AuthSession:
        user = self._identity_repository.get_user_by_id_for_org(org_id=org_id, user_id=user_id)
        membership = self._identity_repository.get_membership(org_id=org_id, user_id=user_id)
        if user is None or membership is None or user.status != UserStatus.active:
            raise UnauthenticatedError("The user cannot authenticate.")
        now = utc_now()
        session = AuthSession(
            org_id=org_id,
            user_id=user_id,
            provider=provider,
            provider_subject=provider_subject,
            client_type=client_type,
            client_name=client_name,
            capabilities=capabilities,
            max_visibility_scope=max_visibility_scope,
            expires_at=now + timedelta(seconds=self._settings.session_seconds),
            last_used_at=now,
        )
        self._repository.add_session(session)
        self._db.flush()
        actor = ActorContext(
            org_id=org_id,
            user_id=user_id,
            session_id=session.id,
            session_capabilities=set(capabilities),
            session_max_visibility_scope=max_visibility_scope,
            client_type=client_type.value,
            request_id="session-created",
        )
        self._audit_service.record_event(
            actor=actor,
            action="auth.session.created",
            resource_type="auth_session",
            resource_id=session.id,
            decision=AuditDecision.allow,
            metadata={"client_type": client_type.value, "client_name": client_name or ""},
        )
        return session

    def build_oidc_authorization_url(self, *, provider: str, redirect_uri: str) -> str:
        self._require_known_provider(provider)
        if redirect_uri not in self._settings.web_login_redirect_uris:
            raise BadRequestError("The redirect_uri is not allowed.")
        provider_client = self._require_oidc_provider()
        nonce = generate_token("nonce", bytes_count=16)
        state = self._encode_oidc_state(redirect_uri=redirect_uri, nonce=nonce)
        return provider_client.build_authorization_url(
            redirect_uri=redirect_uri, state=state, nonce=nonce
        )

    def complete_oidc_login(self, *, provider: str, code: str, state: str) -> str:
        self._require_known_provider(provider)
        redirect_uri, nonce = self._decode_oidc_state(state)
        provider_client = self._require_oidc_provider()
        try:
            identity = provider_client.exchange_code(
                code=code, redirect_uri=redirect_uri, nonce=nonce
            )
        except OidcError:
            return self._login_redirect(redirect_uri, error="oidc_exchange_failed")
        if not identity.email_verified:
            return self._login_redirect(redirect_uri, error="email_not_verified")
        organization = self._identity_repository.get_organization_by_slug(
            self._settings.oidc_org_slug
        )
        if organization is None:
            return self._login_redirect(redirect_uri, error="organization_not_found")
        user = self._identity_repository.get_user_by_email_for_org(
            org_id=organization.id, email=identity.email
        )
        if user is None or user.status != UserStatus.active:
            return self._login_redirect(redirect_uri, error="user_not_authorized")
        session = self._start_session(
            org_id=organization.id,
            user_id=user.id,
            provider="google",
            provider_subject=identity.subject,
            client_type=AuthClientType.web,
            client_name="nexus-web",
            capabilities=[],
            max_visibility_scope=None,
        )
        login_code = generate_token("nxs_wl", bytes_count=32)
        self._repository.add_web_login(
            AuthWebLogin(
                org_id=organization.id,
                user_id=user.id,
                session_id=session.id,
                login_code_hash=hash_secret(login_code, self._settings.token_secret),
                expires_at=utc_now() + timedelta(seconds=self._settings.web_login_seconds),
            )
        )
        self._db.commit()
        return self._login_redirect(redirect_uri, login_code=login_code)

    def exchange_web_login(self, *, login_code: str) -> TokenResponse:
        web_login = self._repository.get_web_login_by_hash(
            hash_secret(login_code, self._settings.token_secret)
        )
        if (
            web_login is None
            or web_login.consumed_at is not None
            or as_utc(web_login.expires_at) <= utc_now()
        ):
            raise UnauthenticatedError("Invalid login code.")
        session = self._repository.get_session(
            org_id=web_login.org_id, session_id=web_login.session_id
        )
        if (
            session is None
            or session.revoked_at is not None
            or as_utc(session.expires_at) <= utc_now()
        ):
            raise UnauthenticatedError("Invalid session.")
        web_login.consumed_at = utc_now()
        response = self._issue_token_pair(session=session, parent_token_id=None)
        self._db.commit()
        return response

    def _require_known_provider(self, provider: str) -> None:
        if provider != "google":
            raise NotFoundError("auth provider")

    def _require_oidc_provider(self) -> OidcProvider:
        if self._oidc_provider is not None:
            return self._oidc_provider
        if not self._settings.oidc_client_id or not self._settings.oidc_client_secret:
            raise NotFoundError("auth provider")
        return build_google_provider(
            client_id=self._settings.oidc_client_id,
            client_secret=self._settings.oidc_client_secret,
        )

    def _encode_oidc_state(self, *, redirect_uri: str, nonce: str) -> str:
        now = utc_now()
        claims: JsonObject = {
            "iss": self._settings.token_issuer,
            "aud": _OIDC_STATE_AUDIENCE,
            "redirect_uri": redirect_uri,
            "nonce": nonce,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self._settings.oidc_state_seconds)).timestamp()),
        }
        return encode_access_token(claims, self._settings.token_secret)

    def _decode_oidc_state(self, state: str) -> tuple[str, str]:
        claims = decode_access_token(state, self._settings.token_secret)
        if claims is None or claims.get("aud") != _OIDC_STATE_AUDIENCE:
            raise BadRequestError("Invalid OIDC state.")
        redirect_uri = claims.get("redirect_uri")
        nonce = claims.get("nonce")
        if (
            not isinstance(redirect_uri, str)
            or redirect_uri not in self._settings.web_login_redirect_uris
            or not isinstance(nonce, str)
        ):
            raise BadRequestError("Invalid OIDC state.")
        return redirect_uri, nonce

    def _login_redirect(
        self, redirect_uri: str, *, login_code: str | None = None, error: str | None = None
    ) -> str:
        parameter = {"login_code": login_code} if login_code is not None else {"error": error}
        return f"{redirect_uri}?{urllib.parse.urlencode(parameter)}"

    def validate_access_token(self, *, token: str, request_id: str) -> ActorContext:
        claims = decode_access_token(token, self._settings.token_secret)
        if claims is None:
            raise UnauthenticatedError("Invalid or expired access token.")
        if (
            claims.get("iss") != self._settings.token_issuer
            or claims.get("aud") != self._settings.token_audience
        ):
            raise UnauthenticatedError("Invalid access token audience.")
        org_id = UUID(str(claims.get("org_id")))
        user_id = UUID(str(claims.get("sub")))
        session_id = UUID(str(claims.get("sid")))
        session = self._repository.get_session(org_id=org_id, session_id=session_id)
        user = self._identity_repository.get_user_by_id_for_org(org_id=org_id, user_id=user_id)
        if session is None or user is None:
            raise UnauthenticatedError("Invalid session.")
        actor = ActorContext(
            org_id=org_id,
            user_id=user_id,
            session_id=session_id,
            session_capabilities=set(session.capabilities),
            session_max_visibility_scope=session.max_visibility_scope,
            client_type=session.client_type.value,
            request_id=request_id,
        )
        if session.revoked_at is not None or as_utc(session.expires_at) <= utc_now():
            self._audit_service.record_denial(actor=actor, reason="revoked_session")
            self._db.commit()
            raise UnauthenticatedError("The session is revoked or expired.")
        if user.status != UserStatus.active:
            self._audit_service.record_denial(actor=actor, reason="inactive_user")
            self._db.commit()
            raise UnauthenticatedError("The user is inactive.")
        session.last_used_at = utc_now()
        self._db.commit()
        return actor

    def refresh_session(self, *, refresh_token: str) -> TokenResponse:
        token_hash = hash_secret(refresh_token, self._settings.token_secret)
        stored = self._repository.get_refresh_token_by_hash(token_hash)
        if (
            stored is None
            or stored.revoked_at is not None
            or as_utc(stored.expires_at) <= utc_now()
        ):
            raise UnauthenticatedError("Invalid refresh token.")
        session = self._repository.get_session(org_id=stored.org_id, session_id=stored.session_id)
        if (
            session is None
            or session.revoked_at is not None
            or as_utc(session.expires_at) <= utc_now()
        ):
            raise UnauthenticatedError("Invalid session.")
        actor = ActorContext(
            org_id=session.org_id,
            user_id=session.user_id,
            session_id=session.id,
            session_capabilities=set(session.capabilities),
            session_max_visibility_scope=session.max_visibility_scope,
            client_type=session.client_type.value,
            request_id="refresh",
        )
        if stored.used_at is not None:
            session.revoked_at = utc_now()
            self._audit_service.record_event(
                actor=actor,
                action="auth.refresh_reuse_detected",
                resource_type="auth_session",
                resource_id=session.id,
                decision=AuditDecision.deny,
                reason="refresh_reuse_detected",
                metadata={"session_id": str(session.id)},
            )
            self._db.commit()
            raise UnauthenticatedError("Refresh token reuse detected.")
        user = self._identity_repository.get_user_by_id_for_org(
            org_id=session.org_id, user_id=session.user_id
        )
        if user is None or user.status != UserStatus.active:
            raise UnauthenticatedError("The user is inactive.")
        stored.used_at = utc_now()
        response = self._issue_token_pair(session=session, parent_token_id=stored.id)
        self._audit_service.record_event(
            actor=actor,
            action="auth.session.refreshed",
            resource_type="auth_session",
            resource_id=session.id,
            decision=AuditDecision.allow,
            metadata={"session_id": str(session.id)},
        )
        self._db.commit()
        return response

    def revoke_session(self, *, actor: ActorContext, session_id: UUID | None = None) -> None:
        target_id = session_id if session_id is not None else actor.session_id
        session = self._repository.get_session(org_id=actor.org_id, session_id=target_id)
        if session is None or session.user_id != actor.user_id:
            raise NotFoundError("auth session")
        session.revoked_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="auth.session.revoked",
            resource_type="auth_session",
            resource_id=session.id,
            decision=AuditDecision.allow,
            metadata={"session_id": str(session.id)},
        )
        self._db.commit()

    def list_sessions(self, *, actor: ActorContext) -> list[AuthSession]:
        return self._repository.list_sessions_for_user(org_id=actor.org_id, user_id=actor.user_id)

    def _issue_token_pair(
        self, *, session: AuthSession, parent_token_id: UUID | None
    ) -> TokenResponse:
        now = utc_now()
        access_expires_at = now + timedelta(seconds=self._settings.access_token_seconds)
        refresh_expires_at = now + timedelta(seconds=self._settings.refresh_token_seconds)
        capabilities: list[JsonValue] = []
        capabilities.extend(session.capabilities)
        claims: JsonObject = {
            "iss": self._settings.token_issuer,
            "aud": self._settings.token_audience,
            "sub": str(session.user_id),
            "org_id": str(session.org_id),
            "sid": str(session.id),
            "client_type": session.client_type.value,
            "capabilities": capabilities,
            "max_visibility_scope": session.max_visibility_scope.value
            if session.max_visibility_scope is not None
            else None,
            "iat": int(now.timestamp()),
            "exp": int(access_expires_at.timestamp()),
            "auth_time": int(session.created_at.timestamp()),
        }
        access_token = encode_access_token(claims, self._settings.token_secret)
        refresh_token = generate_token("nxs_rt", bytes_count=32)
        stored = AuthRefreshToken(
            org_id=session.org_id,
            session_id=session.id,
            token_hash=hash_secret(refresh_token, self._settings.token_secret),
            parent_token_id=parent_token_id,
            expires_at=refresh_expires_at,
        )
        self._repository.add_refresh_token(stored)
        return TokenResponse(
            access_token=access_token,
            expires_in=self._settings.access_token_seconds,
            refresh_token=refresh_token,
            refresh_expires_in=self._settings.refresh_token_seconds,
            session_id=session.id,
            org_id=session.org_id,
            user_id=session.user_id,
            capabilities=session.capabilities,
            max_visibility_scope=session.max_visibility_scope,
        )
