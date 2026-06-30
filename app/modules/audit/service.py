from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.json import JsonObject, JsonValue
from app.modules.audit.models import AuditDecision, AuditEvent
from app.modules.audit.repository import AuditRepository
from app.modules.auth.types import ActorContext

SENSITIVE_KEY_PARTS = ("token", "secret", "code", "body", "rationale", "query", "task")
SAFE_HASH_KEYS = {"query_hash", "task_hash"}


class AuditService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = AuditRepository(db)

    def record_event(
        self,
        *,
        actor: ActorContext | None,
        action: str,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        decision: AuditDecision | None = None,
        reason: str | None = None,
        metadata: JsonObject | None = None,
        org_id: UUID | None = None,
    ) -> AuditEvent:
        event_org_id = org_id if org_id is not None else actor.org_id if actor is not None else None
        if event_org_id is None:
            msg = "audit event requires org id"
            raise ValueError(msg)
        event = AuditEvent(
            org_id=event_org_id,
            actor_user_id=actor.user_id if actor is not None else None,
            actor_session_id=actor.session_id if actor is not None else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision=decision,
            reason=reason,
            request_id=actor.request_id if actor is not None else None,
            metadata_=_sanitize_metadata(metadata or {}),
        )
        return self._repository.add(event)

    def record_denial(
        self,
        *,
        actor: ActorContext,
        reason: str,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        metadata: JsonObject | None = None,
    ) -> AuditEvent:
        safe_metadata: JsonObject = {"reason_code": reason}
        if metadata:
            safe_metadata.update(metadata)
        return self.record_event(
            actor=actor,
            action="authorization.denied",
            resource_type=resource_type,
            resource_id=resource_id,
            decision=AuditDecision.deny,
            reason=reason,
            metadata=safe_metadata,
        )


def _sanitize_metadata(metadata: JsonObject) -> JsonObject:
    return {
        key: _sanitize_value(value)
        for key, value in metadata.items()
        if key in SAFE_HASH_KEYS or not any(part in key.lower() for part in SENSITIVE_KEY_PARTS)
    }


def _sanitize_value(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return _sanitize_metadata(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value
