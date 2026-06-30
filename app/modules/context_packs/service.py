from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.security import hash_text
from app.common.time import utc_now
from app.modules.audit.models import AuditDecision
from app.modules.audit.service import AuditService
from app.modules.auth.types import ActorContext
from app.modules.context_packs.schemas import (
    ContextPackItemResponse,
    ContextPackItemsResponse,
    ContextPackRequest,
    ContextPackResponse,
    ContextPackWarningResponse,
)
from app.modules.memory_entries.models import MemoryStatus, MemoryType
from app.modules.search.schemas import SearchRequest
from app.modules.search.service import SearchService

TYPE_GROUPS = {
    MemoryType.decision: "decisions",
    MemoryType.problem: "problems",
    MemoryType.solution: "solutions",
    MemoryType.failed_attempt: "failed_attempts",
    MemoryType.risk: "risks",
    MemoryType.procedure: "procedures",
    MemoryType.open_question: "open_questions",
    MemoryType.task: "tasks",
    MemoryType.note: "notes",
}
TYPE_ORDER = [
    MemoryType.decision,
    MemoryType.procedure,
    MemoryType.risk,
    MemoryType.problem,
    MemoryType.solution,
    MemoryType.failed_attempt,
    MemoryType.open_question,
    MemoryType.task,
    MemoryType.note,
]


class ContextPackService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._search_service = SearchService(db)
        self._audit_service = AuditService(db)

    def generate(self, *, actor: ActorContext, request: ContextPackRequest) -> ContextPackResponse:
        include_types = request.include_types or TYPE_ORDER[:-2]
        query = request.query or request.task
        search_response = self._search_service.execute_search(
            actor=actor,
            request=SearchRequest(
                query=query,
                project_id=request.project_id,
                types=include_types,
                statuses=[MemoryStatus.active, MemoryStatus.needs_review],
                limit=request.max_items,
                include_evidence=False,
            ),
            audit=False,
        )
        items = ContextPackItemsResponse()
        selected = 0
        warnings: list[ContextPackWarningResponse] = []
        for memory_type in TYPE_ORDER:
            group_name = TYPE_GROUPS[memory_type]
            group_items = [
                result for result in search_response.results if result.type == memory_type
            ]
            for result in group_items:
                if selected >= request.max_items:
                    break
                getattr(items, group_name).append(
                    ContextPackItemResponse(
                        id=result.id,
                        title=result.title,
                        body=result.body,
                        status=result.status,
                        evidence_count=result.evidence_count,
                    )
                )
                selected += 1
                if result.status == MemoryStatus.needs_review and not warnings:
                    warnings.append(
                        ContextPackWarningResponse(
                            type="needs_review",
                            message="Some related memories are marked as needing review.",
                        )
                    )
        self._audit_service.record_event(
            actor=actor,
            action="context_pack.generated",
            decision=AuditDecision.allow,
            metadata={
                "query_hash": hash_text(request.query or ""),
                "task_hash": hash_text(request.task or ""),
                "project_id": str(request.project_id) if request.project_id is not None else None,
                "max_items": request.max_items,
                "result_count": selected,
                "warning_count": len(warnings),
            },
        )
        self._db.commit()
        return ContextPackResponse(
            project_id=request.project_id,
            generated_at=utc_now(),
            items=items,
            warnings=warnings,
        )
