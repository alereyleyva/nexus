from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.errors import BadRequestError, ValidationProblem
from app.common.pagination import PageInfo
from app.common.security import hash_text
from app.common.time import as_utc, utc_now
from app.modules.audit.models import AuditDecision
from app.modules.audit.service import AuditService
from app.modules.auth.types import ActorContext
from app.modules.authorization.service import AuthorizationService
from app.modules.memory_entries.models import DEFAULT_READ_STATUSES, MemoryEntry, MemoryStatus
from app.modules.memory_entries.repository import MemoryEntryRepository
from app.modules.search.schemas import SearchRequest, SearchResponse, SearchResultResponse

EXPLICIT_SEARCH_STATUSES = {
    MemoryStatus.active,
    MemoryStatus.needs_review,
    MemoryStatus.deprecated,
    MemoryStatus.archived,
}


class SearchService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._authorization = AuthorizationService(db)
        self._repository = MemoryEntryRepository(db)
        self._audit_service = AuditService(db)

    def search(self, *, actor: ActorContext, request: SearchRequest) -> SearchResponse:
        return self.execute_search(actor=actor, request=request, audit=True)

    def execute_search(
        self, *, actor: ActorContext, request: SearchRequest, audit: bool
    ) -> SearchResponse:
        if not request.query and not any(
            [request.project_id, request.types, request.statuses, request.tags]
        ):
            raise BadRequestError("Search requires a query or at least one structured filter.")
        statuses = tuple(request.statuses) if request.statuses else DEFAULT_READ_STATUSES
        if any(status not in EXPLICIT_SEARCH_STATUSES for status in statuses):
            raise ValidationProblem("Search cannot include pending or rejected memory statuses.")
        statement = self._authorization.readable_memory_statement(actor, statuses)
        if request.project_id is not None:
            statement = statement.where(MemoryEntry.project_id == request.project_id)
        if request.types:
            statement = statement.where(MemoryEntry.type.in_(request.types))
        if request.query and self._db.get_bind().dialect.name == "postgresql":
            statement = statement.where(
                MemoryEntry.search_vector.op("@@")(
                    func.websearch_to_tsquery("simple", request.query)
                )
            )
        statement = statement.order_by(MemoryEntry.updated_at.desc(), MemoryEntry.id.desc())
        candidates = self._repository.list_by_statement(statement, limit=request.limit * 5 + 10)
        filtered = [memory for memory in candidates if self._matches(memory, request)]
        ranked = sorted(
            filtered, key=lambda memory: self._score(memory, request.query), reverse=True
        )
        page_items = ranked[: request.limit]
        results = [self._result(memory=memory, query=request.query) for memory in page_items]
        if audit:
            self._audit_service.record_event(
                actor=actor,
                action="search.executed",
                resource_type=None,
                resource_id=None,
                decision=AuditDecision.allow,
                metadata={
                    "query_hash": hash_text(request.query or ""),
                    "project_id": str(request.project_id)
                    if request.project_id is not None
                    else None,
                    "types": [item.value for item in request.types],
                    "statuses": [item.value for item in statuses],
                    "tag_count": len(request.tags),
                    "result_count": len(results),
                },
            )
            self._db.commit()
        return SearchResponse(
            results=results,
            page=PageInfo(next_cursor=None, has_more=len(ranked) > request.limit),
        )

    def _matches(self, memory: MemoryEntry, request: SearchRequest) -> bool:
        if request.tags and not all(tag in memory.tags for tag in request.tags):
            return False
        if request.query:
            text = (
                f"{memory.title} {memory.body} {memory.rationale or ''} {' '.join(memory.tags)}"
            ).lower()
            return all(part.lower() in text for part in request.query.split())
        return True

    def _score(self, memory: MemoryEntry, query: str | None) -> float:
        text_rank = self._text_rank(memory, query)
        age_days = (utc_now() - as_utc(memory.updated_at)).days
        freshness = 1.0 if age_days <= 30 else 0.5 if age_days <= 180 else 0.0
        type_priority = {
            "decision": 1.0,
            "procedure": 1.0,
            "risk": 1.0,
            "problem": 0.75,
            "solution": 0.75,
            "failed_attempt": 0.75,
            "open_question": 0.5,
            "task": 0.5,
            "note": 0.25,
        }[memory.type.value]
        status_score = {
            MemoryStatus.active: 1.0,
            MemoryStatus.needs_review: 0.5,
            MemoryStatus.deprecated: 0.25,
            MemoryStatus.archived: 0.0,
            MemoryStatus.pending_review: 0.0,
            MemoryStatus.rejected: 0.0,
        }[memory.status]
        return text_rank * 0.75 + freshness * 0.10 + type_priority * 0.10 + status_score * 0.05

    def _text_rank(self, memory: MemoryEntry, query: str | None) -> float:
        if not query:
            return 0.0
        text = (
            f"{memory.title} {memory.body} {memory.rationale or ''} {' '.join(memory.tags)}".lower()
        )
        parts = query.lower().split()
        if not parts:
            return 0.0
        return sum(1 for part in parts if part in text) / len(parts)

    def _result(self, *, memory: MemoryEntry, query: str | None) -> SearchResultResponse:
        return SearchResultResponse(
            id=memory.id,
            type=memory.type,
            title=memory.title,
            body=memory.body,
            status=memory.status,
            visibility_scope=memory.visibility_scope,
            project_id=memory.project_id,
            tags=memory.tags,
            score=self._score(memory, query),
            evidence_count=self._repository.evidence_count(
                org_id=memory.org_id, memory_id=memory.id
            ),
            needs_review_warning=memory.status == MemoryStatus.needs_review,
        )
