from __future__ import annotations

from collections.abc import Sequence
from typing import NoReturn
from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.errors import (
    AuthorizationDeniedError,
    ConflictError,
    NotFoundError,
    ValidationProblem,
)
from app.common.json import JsonValue
from app.common.pagination import PageInfo
from app.common.time import utc_now
from app.modules.audit.models import AuditDecision
from app.modules.audit.service import AuditService
from app.modules.auth.types import ActorContext
from app.modules.authorization.service import AuthorizationService, CreationDecision
from app.modules.identity.repository import IdentityRepository
from app.modules.memory_entries.models import (
    DEFAULT_READ_STATUSES,
    MemoryEntry,
    MemoryEntryEvidence,
    MemoryEntryGrant,
    MemoryStatus,
    VisibilityScope,
)
from app.modules.memory_entries.repository import MemoryEntryRepository, build_search_document
from app.modules.memory_entries.schemas import (
    AddGrantRequest,
    BulkCreateMemoryEntriesRequest,
    BulkCreateMemoryEntriesResponse,
    ChangeVisibilityRequest,
    CreateMemoryEntryRequest,
    EvidenceResponse,
    GrantResponse,
    MemoryEntryListResponse,
    MemoryEntryResponse,
    MemoryMutationResponse,
    ReviewMemoryEntryRequest,
    UpdateMemoryEntryRequest,
)


class MemoryEntryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = MemoryEntryRepository(db)
        self._authorization = AuthorizationService(db)
        self._audit_service = AuditService(db)
        self._identity_repository = IdentityRepository(db)

    def create_memory(
        self, *, actor: ActorContext, request: CreateMemoryEntryRequest
    ) -> MemoryMutationResponse:
        decision = self._creation_decision(actor=actor, request=request)
        if request.client_entry_id is not None:
            existing = self._repository.get_by_client_entry_id(
                org_id=actor.org_id,
                created_by_user_id=actor.user_id,
                source_tool=request.source_tool,
                client_entry_id=request.client_entry_id,
            )
            if existing is not None:
                return _mutation_response(
                    existing, requires_review=existing.status == MemoryStatus.pending_review
                )
        memory = self._build_memory(actor=actor, request=request, decision=decision)
        try:
            self._repository.add(memory)
            self._db.flush()
            self._add_evidence(actor=actor, memory=memory, request=request)
            self._refresh_search_vector(memory)
            self._audit_service.record_event(
                actor=actor,
                action="memory_entry.created",
                resource_type="memory_entry",
                resource_id=memory.id,
                decision=AuditDecision.allow,
                metadata={
                    "visibility_scope": memory.visibility_scope.value,
                    "status_after": memory.status.value,
                    "project_id": str(memory.project_id) if memory.project_id is not None else None,
                    "memory_type": memory.type.value,
                    "source_tool": memory.source_tool,
                },
            )
            self._db.commit()
        except IntegrityError as exc:
            self._db.rollback()
            raise ConflictError("The memory entry conflicts with an existing record.") from exc
        return _mutation_response(memory, requires_review=decision.requires_review)

    def bulk_create_memory(
        self, *, actor: ActorContext, request: BulkCreateMemoryEntriesRequest
    ) -> BulkCreateMemoryEntriesResponse:
        decisions = [
            self._creation_decision(actor=actor, request=entry) for entry in request.entries
        ]
        created: list[MemoryEntry] = []
        try:
            for entry_request, decision in zip(request.entries, decisions, strict=True):
                memory = self._build_memory(actor=actor, request=entry_request, decision=decision)
                self._repository.add(memory)
                self._db.flush()
                self._add_evidence(actor=actor, memory=memory, request=entry_request)
                self._refresh_search_vector(memory)
                self._audit_service.record_event(
                    actor=actor,
                    action="memory_entry.created",
                    resource_type="memory_entry",
                    resource_id=memory.id,
                    decision=AuditDecision.allow,
                    metadata={
                        "visibility_scope": memory.visibility_scope.value,
                        "status_after": memory.status.value,
                        "memory_type": memory.type.value,
                    },
                )
                created.append(memory)
            self._db.commit()
        except (IntegrityError, AuthorizationDeniedError, ValidationProblem) as exc:
            self._db.rollback()
            if isinstance(exc, IntegrityError):
                raise ConflictError(
                    "A bulk memory entry conflicts with an existing record."
                ) from exc
            raise
        return BulkCreateMemoryEntriesResponse(
            items=[
                _mutation_response(
                    memory, requires_review=memory.status == MemoryStatus.pending_review
                )
                for memory in created
            ]
        )

    def get_memory(self, *, actor: ActorContext, memory_id: UUID) -> MemoryEntryResponse:
        statement = self._authorization.readable_memory_statement(actor)
        memory = self._repository.get_by_readable_statement(statement, memory_id=memory_id)
        if memory is None:
            self._record_hidden_denial(
                actor=actor, memory_id=memory_id, reason="visibility_audience_miss"
            )
        return self._response(memory, include_evidence=True)

    def list_memory(
        self,
        *,
        actor: ActorContext,
        project_id: UUID | None = None,
        limit: int = 50,
        statuses: Sequence[MemoryStatus] | None = None,
    ) -> MemoryEntryListResponse:
        allowed_statuses = tuple(statuses) if statuses is not None else DEFAULT_READ_STATUSES
        statement = self._authorization.readable_memory_statement(actor, allowed_statuses)
        if project_id is not None:
            statement = statement.where(MemoryEntry.project_id == project_id)
        statement = statement.order_by(MemoryEntry.updated_at.desc(), MemoryEntry.id.desc())
        items = self._repository.list_by_statement(statement, limit=limit + 1)
        visible_items = items[:limit]
        return MemoryEntryListResponse(
            items=[self._response(memory, include_evidence=False) for memory in visible_items],
            page=PageInfo(next_cursor=None, has_more=len(items) > limit),
        )

    def update_memory(
        self, *, actor: ActorContext, memory_id: UUID, request: UpdateMemoryEntryRequest
    ) -> MemoryEntryResponse:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        if not self._authorization.can_edit_memory(actor=actor, memory=memory):
            self._record_operation_denial(actor=actor, memory=memory, reason="not_owner_or_manager")
        changed_fields: list[str] = []
        for field in ("title", "body", "rationale", "tags", "metadata", "source_context"):
            value = getattr(request, field)
            if value is not None:
                target_field = "metadata_" if field == "metadata" else field
                setattr(memory, target_field, value)
                changed_fields.append(field)
        memory.updated_at = utc_now()
        self._refresh_search_vector(memory)
        changed_values: list[JsonValue] = []
        changed_values.extend(changed_fields)
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.updated",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={"field_names_changed": changed_values, "status_after": memory.status.value},
        )
        self._db.commit()
        return self._response(memory, include_evidence=True)

    def review_memory(
        self, *, actor: ActorContext, memory_id: UUID, request: ReviewMemoryEntryRequest
    ) -> MemoryMutationResponse:
        memory = self._repository.get_by_id_for_org(org_id=actor.org_id, memory_id=memory_id)
        if memory is None:
            raise NotFoundError("memory entry")
        if not self._authorization.can_review_memory(actor=actor, memory=memory):
            reason = (
                "self_review_denied" if memory.owner_user_id == actor.user_id else "not_reviewer"
            )
            self._record_operation_denial(actor=actor, memory=memory, reason=reason)
        if request.decision == "reject" and memory.status != MemoryStatus.pending_review:
            raise ConflictError("Only pending review memory can be rejected.")
        memory.status = (
            MemoryStatus.active if request.decision == "approve" else MemoryStatus.rejected
        )
        memory.reviewed_by_user_id = actor.user_id
        memory.review_comment = request.review_comment
        memory.reviewed_at = utc_now()
        memory.updated_at = utc_now()
        action = (
            "memory_entry.approved" if request.decision == "approve" else "memory_entry.rejected"
        )
        self._audit_service.record_event(
            actor=actor,
            action=action,
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={"status_after": memory.status.value},
        )
        self._db.commit()
        return _mutation_response(memory, requires_review=False)

    def mark_needs_review(
        self, *, actor: ActorContext, memory_id: UUID, reason: str | None
    ) -> MemoryMutationResponse:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        if memory.status != MemoryStatus.active:
            raise ConflictError("Only active memory can be marked needs review.")
        if not self._authorization.can_archive_memory(actor=actor, memory=memory):
            self._record_operation_denial(actor=actor, memory=memory, reason="not_reviewer")
        memory.status = MemoryStatus.needs_review
        memory.updated_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.marked_needs_review",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={"status_after": memory.status.value, "reason_code": reason or "not_provided"},
        )
        self._db.commit()
        return _mutation_response(memory, requires_review=True)

    def deprecate_memory(
        self, *, actor: ActorContext, memory_id: UUID, reason: str | None
    ) -> MemoryMutationResponse:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        if memory.status not in {MemoryStatus.active, MemoryStatus.needs_review}:
            raise ConflictError("Only active or needs review memory can be deprecated.")
        if not self._authorization.can_archive_memory(actor=actor, memory=memory):
            self._record_operation_denial(actor=actor, memory=memory, reason="not_reviewer")
        memory.status = MemoryStatus.deprecated
        memory.updated_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.deprecated",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={"status_after": memory.status.value, "reason_code": reason or "not_provided"},
        )
        self._db.commit()
        return _mutation_response(memory, requires_review=False)

    def archive_memory(
        self, *, actor: ActorContext, memory_id: UUID, reason: str | None
    ) -> MemoryMutationResponse:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        if not self._authorization.can_archive_memory(actor=actor, memory=memory):
            self._record_operation_denial(actor=actor, memory=memory, reason="not_reviewer")
        memory.status = MemoryStatus.archived
        memory.updated_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.archived",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={"status_after": memory.status.value, "reason_code": reason or "not_provided"},
        )
        self._db.commit()
        return _mutation_response(memory, requires_review=False)

    def soft_delete_memory(self, *, actor: ActorContext, memory_id: UUID) -> None:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        if (
            memory.visibility_scope not in {VisibilityScope.private, VisibilityScope.restricted}
            and memory.status != MemoryStatus.pending_review
        ):
            raise ConflictError("Active shared memory must be archived instead of deleted.")
        if not self._authorization.can_soft_delete_memory(actor=actor, memory=memory):
            self._record_operation_denial(actor=actor, memory=memory, reason="not_owner_or_manager")
        memory.deleted_at = utc_now()
        memory.updated_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.deleted",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={"status_before": memory.status.value},
        )
        self._db.commit()

    def change_visibility(
        self, *, actor: ActorContext, memory_id: UUID, request: ChangeVisibilityRequest
    ) -> MemoryMutationResponse:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        before_status = memory.status
        decision = self._authorization.decide_visibility_change(
            actor=actor,
            memory=memory,
            target_scope=request.visibility_scope,
            project_id=request.project_id,
            visibility_group_id=request.visibility_group_id,
        )
        memory.visibility_scope = request.visibility_scope
        memory.project_id = request.project_id
        memory.visibility_group_id = request.visibility_group_id
        memory.status = decision.status
        memory.updated_at = utc_now()
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.visibility_changed",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={
                "visibility_scope": memory.visibility_scope.value,
                "status_before": before_status.value,
                "status_after": memory.status.value,
                "reason_code": request.reason or "not_provided",
            },
        )
        self._db.commit()
        return _mutation_response(memory, requires_review=decision.requires_review)

    def add_grant(
        self, *, actor: ActorContext, memory_id: UUID, request: AddGrantRequest
    ) -> GrantResponse:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        if memory.visibility_scope != VisibilityScope.restricted:
            raise ValidationProblem("Grants only apply to restricted memory.")
        if not self._authorization.can_manage_grants(actor=actor, memory=memory):
            self._record_operation_denial(actor=actor, memory=memory, reason="not_owner_or_manager")
        user = self._identity_repository.get_user_by_id_for_org(
            org_id=actor.org_id, user_id=request.grantee_user_id
        )
        if user is None:
            raise ValidationProblem("Grant target user does not exist in the organization.")
        if (
            self._repository.get_grant_for_user(
                org_id=actor.org_id, memory_id=memory.id, user_id=request.grantee_user_id
            )
            is not None
        ):
            raise ConflictError("The user already has a grant for this memory entry.")
        grant = MemoryEntryGrant(
            org_id=actor.org_id,
            memory_entry_id=memory.id,
            grantee_user_id=request.grantee_user_id,
            role=request.role,
            created_by_user_id=actor.user_id,
        )
        self._repository.add_grant(grant)
        self._db.flush()
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.grant_added",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={
                "grant_id": str(grant.id),
                "grantee_user_id": str(grant.grantee_user_id),
                "grant_role": grant.role.value,
            },
        )
        self._db.commit()
        return GrantResponse.model_validate(grant)

    def delete_grant(self, *, actor: ActorContext, memory_id: UUID, grant_id: UUID) -> None:
        memory = self._get_mutation_target(actor=actor, memory_id=memory_id)
        if not self._authorization.can_manage_grants(actor=actor, memory=memory):
            self._record_operation_denial(actor=actor, memory=memory, reason="not_owner_or_manager")
        grant = self._repository.get_grant(org_id=actor.org_id, grant_id=grant_id)
        if grant is None or grant.memory_entry_id != memory.id:
            raise NotFoundError("memory entry grant")
        self._repository.delete_grant(grant)
        self._audit_service.record_event(
            actor=actor,
            action="memory_entry.grant_removed",
            resource_type="memory_entry",
            resource_id=memory.id,
            decision=AuditDecision.allow,
            metadata={"grant_id": str(grant.id), "grantee_user_id": str(grant.grantee_user_id)},
        )
        self._db.commit()

    def review_queue(self, *, actor: ActorContext, limit: int = 50) -> MemoryEntryListResponse:
        statement = self._authorization.reviewable_memory_statement(actor).order_by(
            MemoryEntry.created_at.asc(), MemoryEntry.id.asc()
        )
        items = self._repository.list_by_statement(statement, limit=limit + 1)
        visible_items = items[:limit]
        return MemoryEntryListResponse(
            items=[self._response(memory, include_evidence=True) for memory in visible_items],
            page=PageInfo(next_cursor=None, has_more=len(items) > limit),
        )

    def _creation_decision(
        self, *, actor: ActorContext, request: CreateMemoryEntryRequest
    ) -> CreationDecision:
        scope = request.visibility_scope or VisibilityScope.private
        try:
            return self._authorization.can_create_memory(
                actor=actor,
                visibility_scope=scope,
                project_id=request.project_id,
                visibility_group_id=request.visibility_group_id,
            )
        except AuthorizationDeniedError:
            self._audit_service.record_denial(
                actor=actor,
                reason="visibility_audience_miss",
                metadata={"visibility_scope": scope.value},
            )
            self._db.commit()
            raise

    def _build_memory(
        self,
        *,
        actor: ActorContext,
        request: CreateMemoryEntryRequest,
        decision: CreationDecision,
    ) -> MemoryEntry:
        return MemoryEntry(
            org_id=actor.org_id,
            project_id=request.project_id,
            owner_user_id=actor.user_id,
            created_by_user_id=actor.user_id,
            submitted_via_session_id=actor.session_id,
            type=request.type,
            title=request.title,
            body=request.body,
            rationale=request.rationale,
            status=decision.status,
            visibility_scope=request.visibility_scope or VisibilityScope.private,
            visibility_group_id=request.visibility_group_id,
            source_kind=request.source_kind,
            source_tool=request.source_tool,
            source_ref=request.source_ref,
            client_entry_id=request.client_entry_id,
            confidence=request.confidence,
            tags=request.tags,
            source_context=request.source_context,
            metadata_=request.metadata,
        )

    def _add_evidence(
        self, *, actor: ActorContext, memory: MemoryEntry, request: CreateMemoryEntryRequest
    ) -> None:
        for evidence in request.evidence:
            self._repository.add_evidence(
                MemoryEntryEvidence(
                    org_id=actor.org_id,
                    memory_entry_id=memory.id,
                    kind=evidence.kind,
                    title=evidence.title,
                    quote=evidence.quote,
                    url=evidence.url,
                    locator=evidence.locator,
                    metadata_=evidence.metadata,
                )
            )

    def _get_mutation_target(self, *, actor: ActorContext, memory_id: UUID) -> MemoryEntry:
        memory = self._repository.get_by_id_for_org(org_id=actor.org_id, memory_id=memory_id)
        if memory is None or memory.deleted_at is not None:
            raise NotFoundError("memory entry")
        if not self._authorization.can_read_memory(
            actor=actor,
            memory=memory,
            statuses=(
                MemoryStatus.active,
                MemoryStatus.needs_review,
                MemoryStatus.pending_review,
                MemoryStatus.deprecated,
                MemoryStatus.rejected,
                MemoryStatus.archived,
            ),
        ):
            self._record_hidden_denial(
                actor=actor, memory_id=memory_id, reason="visibility_audience_miss"
            )
        return memory

    def _record_hidden_denial(
        self, *, actor: ActorContext, memory_id: UUID, reason: str
    ) -> NoReturn:
        self._audit_service.record_denial(
            actor=actor,
            reason=reason,
            resource_type="memory_entry",
            resource_id=memory_id,
        )
        self._db.commit()
        raise NotFoundError("memory entry")

    def _record_operation_denial(
        self, *, actor: ActorContext, memory: MemoryEntry, reason: str
    ) -> NoReturn:
        self._audit_service.record_denial(
            actor=actor,
            reason=reason,
            resource_type="memory_entry",
            resource_id=memory.id,
        )
        self._db.commit()
        raise AuthorizationDeniedError()

    def _refresh_search_vector(self, memory: MemoryEntry) -> None:
        bind = self._db.get_bind()
        if bind.dialect.name == "postgresql":
            title_vector = func.setweight(
                func.to_tsvector("simple", func.coalesce(MemoryEntry.title, "")), "A"
            )
            body_vector = func.setweight(
                func.to_tsvector("simple", func.coalesce(MemoryEntry.body, "")), "B"
            )
            rationale_vector = func.setweight(
                func.to_tsvector("simple", func.coalesce(MemoryEntry.rationale, "")), "C"
            )
            tags_vector = func.setweight(
                func.to_tsvector("simple", func.array_to_string(MemoryEntry.tags, " ")), "B"
            )
            search_vector = (
                title_vector.op("||")(body_vector).op("||")(rationale_vector).op("||")(tags_vector)
            )
            self._db.execute(
                update(MemoryEntry)
                .where(MemoryEntry.id == memory.id)
                .values(search_vector=search_vector)
            )
            return
        memory.search_vector = build_search_document(memory)

    def _response(self, memory: MemoryEntry, *, include_evidence: bool) -> MemoryEntryResponse:
        evidence_count = self._repository.evidence_count(org_id=memory.org_id, memory_id=memory.id)
        evidence = (
            [
                EvidenceResponse.model_validate(row)
                for row in self._repository.list_evidence(org_id=memory.org_id, memory_id=memory.id)
            ]
            if include_evidence
            else []
        )
        response = MemoryEntryResponse.model_validate(memory)
        return response.model_copy(
            update={
                "evidence_count": evidence_count,
                "needs_review_warning": memory.status == MemoryStatus.needs_review,
                "evidence": evidence,
            }
        )


def _mutation_response(memory: MemoryEntry, *, requires_review: bool) -> MemoryMutationResponse:
    return MemoryMutationResponse(
        id=memory.id,
        status=memory.status,
        visibility_scope=memory.visibility_scope,
        requires_review=requires_review,
    )
