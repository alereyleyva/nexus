from __future__ import annotations

from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.modules.auth.types import ActorContext
from app.modules.authorization.service import readable_memory_statement
from app.modules.memory_entries.models import DEFAULT_READ_STATUSES, MemoryEntry, MemoryStatus


def readable_memory_query(
    db: Session,
    *,
    actor: ActorContext,
    statuses: tuple[MemoryStatus, ...] = DEFAULT_READ_STATUSES,
) -> Select[tuple[MemoryEntry]]:
    return readable_memory_statement(db, actor=actor, statuses=statuses)
