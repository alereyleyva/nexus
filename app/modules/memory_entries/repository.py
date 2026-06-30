from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.memory_entries.models import (
    MemoryEntry,
    MemoryEntryEvidence,
    MemoryEntryGrant,
    MemoryStatus,
)


class MemoryEntryRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, memory: MemoryEntry) -> MemoryEntry:
        self._db.add(memory)
        return memory

    def add_evidence(self, evidence: MemoryEntryEvidence) -> MemoryEntryEvidence:
        self._db.add(evidence)
        return evidence

    def add_grant(self, grant: MemoryEntryGrant) -> MemoryEntryGrant:
        self._db.add(grant)
        return grant

    def delete_grant(self, grant: MemoryEntryGrant) -> None:
        self._db.delete(grant)

    def get_by_id_for_org(self, *, org_id: UUID, memory_id: UUID) -> MemoryEntry | None:
        return self._db.execute(
            select(MemoryEntry).where(MemoryEntry.org_id == org_id, MemoryEntry.id == memory_id)
        ).scalar_one_or_none()

    def get_by_client_entry_id(
        self, *, org_id: UUID, created_by_user_id: UUID, source_tool: str, client_entry_id: str
    ) -> MemoryEntry | None:
        return self._db.execute(
            select(MemoryEntry).where(
                MemoryEntry.org_id == org_id,
                MemoryEntry.created_by_user_id == created_by_user_id,
                MemoryEntry.source_tool == source_tool,
                MemoryEntry.client_entry_id == client_entry_id,
            )
        ).scalar_one_or_none()

    def get_by_readable_statement(
        self, statement: Select[tuple[MemoryEntry]], *, memory_id: UUID
    ) -> MemoryEntry | None:
        return self._db.execute(statement.where(MemoryEntry.id == memory_id)).scalar_one_or_none()

    def list_by_statement(
        self, statement: Select[tuple[MemoryEntry]], *, limit: int
    ) -> list[MemoryEntry]:
        return list(self._db.execute(statement.limit(limit)).scalars().all())

    def evidence_count(self, *, org_id: UUID, memory_id: UUID) -> int:
        count = self._db.execute(
            select(func.count())
            .select_from(MemoryEntryEvidence)
            .where(
                MemoryEntryEvidence.org_id == org_id,
                MemoryEntryEvidence.memory_entry_id == memory_id,
            )
        ).scalar_one()
        return int(count)

    def list_evidence(self, *, org_id: UUID, memory_id: UUID) -> list[MemoryEntryEvidence]:
        return list(
            self._db.execute(
                select(MemoryEntryEvidence).where(
                    MemoryEntryEvidence.org_id == org_id,
                    MemoryEntryEvidence.memory_entry_id == memory_id,
                )
            )
            .scalars()
            .all()
        )

    def get_grant(self, *, org_id: UUID, grant_id: UUID) -> MemoryEntryGrant | None:
        return self._db.execute(
            select(MemoryEntryGrant).where(
                MemoryEntryGrant.org_id == org_id,
                MemoryEntryGrant.id == grant_id,
            )
        ).scalar_one_or_none()

    def get_grant_for_user(
        self, *, org_id: UUID, memory_id: UUID, user_id: UUID
    ) -> MemoryEntryGrant | None:
        return self._db.execute(
            select(MemoryEntryGrant).where(
                MemoryEntryGrant.org_id == org_id,
                MemoryEntryGrant.memory_entry_id == memory_id,
                MemoryEntryGrant.grantee_user_id == user_id,
            )
        ).scalar_one_or_none()

    def count_by_statuses(self, *, org_id: UUID, statuses: Sequence[MemoryStatus]) -> int:
        count = self._db.execute(
            select(func.count())
            .select_from(MemoryEntry)
            .where(
                MemoryEntry.org_id == org_id,
                MemoryEntry.status.in_(list(statuses)),
                MemoryEntry.deleted_at.is_(None),
            )
        ).scalar_one()
        return int(count)


def build_search_document(memory: MemoryEntry) -> str:
    return " ".join(
        part
        for part in [memory.title, memory.body, memory.rationale or "", " ".join(memory.tags)]
        if part
    )
