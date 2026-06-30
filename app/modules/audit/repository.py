from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, event: AuditEvent) -> AuditEvent:
        self._db.add(event)
        return event

    def list_for_org(self, *, org_id: UUID) -> list[AuditEvent]:
        return list(
            self._db.execute(
                select(AuditEvent)
                .where(AuditEvent.org_id == org_id)
                .order_by(AuditEvent.created_at)
            )
            .scalars()
            .all()
        )
