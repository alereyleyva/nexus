from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import (
    AuthCliAuthorization,
    AuthRefreshToken,
    AuthSession,
    AuthWebLogin,
)


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add_session(self, session: AuthSession) -> AuthSession:
        self._db.add(session)
        return session

    def add_cli_authorization(self, authorization: AuthCliAuthorization) -> AuthCliAuthorization:
        self._db.add(authorization)
        return authorization

    def add_refresh_token(self, token: AuthRefreshToken) -> AuthRefreshToken:
        self._db.add(token)
        return token

    def get_session(self, *, org_id: UUID, session_id: UUID) -> AuthSession | None:
        return self._db.execute(
            select(AuthSession).where(AuthSession.org_id == org_id, AuthSession.id == session_id)
        ).scalar_one_or_none()

    def list_sessions_for_user(self, *, org_id: UUID, user_id: UUID) -> list[AuthSession]:
        return list(
            self._db.execute(
                select(AuthSession).where(
                    AuthSession.org_id == org_id,
                    AuthSession.user_id == user_id,
                    AuthSession.revoked_at.is_(None),
                )
            )
            .scalars()
            .all()
        )

    def add_web_login(self, web_login: AuthWebLogin) -> AuthWebLogin:
        self._db.add(web_login)
        return web_login

    def get_web_login_by_hash(self, login_code_hash: str) -> AuthWebLogin | None:
        return self._db.execute(
            select(AuthWebLogin).where(AuthWebLogin.login_code_hash == login_code_hash)
        ).scalar_one_or_none()

    def get_refresh_token_by_hash(self, token_hash: str) -> AuthRefreshToken | None:
        return self._db.execute(
            select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash)
        ).scalar_one_or_none()

    def get_cli_authorization_by_device_hash(
        self, device_code_hash: str
    ) -> AuthCliAuthorization | None:
        return self._db.execute(
            select(AuthCliAuthorization).where(
                AuthCliAuthorization.device_code_hash == device_code_hash
            )
        ).scalar_one_or_none()

    def get_cli_authorization_by_user_hash(
        self, user_code_hash: str
    ) -> AuthCliAuthorization | None:
        return self._db.execute(
            select(AuthCliAuthorization).where(
                AuthCliAuthorization.user_code_hash == user_code_hash
            )
        ).scalar_one_or_none()
