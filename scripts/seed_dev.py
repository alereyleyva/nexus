"""Seed a local development organization with demo memory for the web UI.

Run from the repository root against the local PostgreSQL instance:

    uv run python -m scripts.seed_dev

The script is idempotent: identity/group/project records are created only when
missing, and demo memory entries are inserted only when the project has none.
It is developer automation only and must never run against production data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.common.json import JsonObject
from app.db.base import load_all_models
from app.db.session import SessionLocal
from app.modules.groups.models import Group, GroupMembership, GroupRole, GroupType
from app.modules.identity.models import (
    Organization,
    OrgMembership,
    OrgRole,
    User,
    UserStatus,
)
from app.modules.memory_entries.models import (
    EvidenceKind,
    MemoryEntry,
    MemoryEntryEvidence,
    MemoryStatus,
    MemoryType,
    SourceKind,
    VisibilityScope,
)
from app.modules.memory_entries.repository import postgres_search_vector
from app.modules.projects.models import (
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectStatus,
)

ORG_SLUG = "aircury"
PROJECT_KEY = "CECW"
GROUP_SLUG = "engineering"


@dataclass(frozen=True)
class SeededIdentity:
    org_id: UUID
    group_id: UUID
    project_id: UUID
    pablo_id: UUID
    fabio_id: UUID
    carlos_id: UUID


def seed() -> None:
    load_all_models()
    session = SessionLocal()
    try:
        identity = _seed_identity(session)
        _seed_memory(session, identity)
        session.commit()
        _print_summary(session, identity)
    finally:
        session.close()


def _seed_identity(session: Session) -> SeededIdentity:
    org = _get_or_create(
        session,
        Organization,
        {"slug": ORG_SLUG},
        Organization(slug=ORG_SLUG, name="Aircury"),
    )
    session.flush()
    pablo = _get_or_create_user(session, org.id, "pablo@aircury.com", "Pablo Ferrer")
    fabio = _get_or_create_user(session, org.id, "fabio@aircury.com", "Fabio Nardi")
    carlos = _get_or_create_user(session, org.id, "carlos@aircury.com", "Carlos Ibáñez")
    session.flush()
    _set_org_membership(session, org.id, pablo.id, OrgRole.knowledge_admin, is_org_admin=True)
    _set_org_membership(session, org.id, fabio.id, OrgRole.member, is_org_admin=False)
    _set_org_membership(session, org.id, carlos.id, OrgRole.member, is_org_admin=False)
    group = _get_or_create(
        session,
        Group,
        {"org_id": org.id, "slug": GROUP_SLUG},
        Group(
            org_id=org.id,
            slug=GROUP_SLUG,
            name="Engineering",
            group_type=GroupType.team,
        ),
    )
    session.flush()
    _set_group_membership(session, org.id, group.id, pablo.id, GroupRole.lead)
    _set_group_membership(session, org.id, group.id, fabio.id, GroupRole.member)
    project = _get_or_create(
        session,
        Project,
        {"org_id": org.id, "key": PROJECT_KEY},
        Project(
            org_id=org.id,
            owning_group_id=group.id,
            key=PROJECT_KEY,
            name="CECW Payments Platform",
            description="Payment synchronization and reconciliation for CECW.",
            status=ProjectStatus.active,
        ),
    )
    session.flush()
    _set_project_membership(session, org.id, project.id, carlos.id, ProjectRole.viewer)
    return SeededIdentity(
        org_id=org.id,
        group_id=group.id,
        project_id=project.id,
        pablo_id=pablo.id,
        fabio_id=fabio.id,
        carlos_id=carlos.id,
    )


def _seed_memory(session: Session, identity: SeededIdentity) -> None:
    existing = session.execute(
        select(func.count()).select_from(MemoryEntry).where(MemoryEntry.org_id == identity.org_id)
    ).scalar_one()
    if int(existing) > 0:
        return
    for spec in _memory_specs(identity):
        entry = MemoryEntry(
            org_id=identity.org_id,
            project_id=spec.project_id,
            owner_user_id=spec.owner_id,
            created_by_user_id=spec.owner_id,
            type=spec.type,
            title=spec.title,
            body=spec.body,
            rationale=spec.rationale,
            status=spec.status,
            visibility_scope=spec.visibility_scope,
            source_kind=SourceKind.ai_cli,
            source_tool=spec.source_tool,
            source_ref=spec.source_ref,
            confidence=spec.confidence,
            tags=list(spec.tags),
            source_context=dict(spec.source_context),
        )
        session.add(entry)
        session.flush()
        for evidence in spec.evidence:
            session.add(
                MemoryEntryEvidence(
                    org_id=identity.org_id,
                    memory_entry_id=entry.id,
                    kind=evidence[0],
                    title=evidence[1],
                    quote=evidence[2],
                    locator=dict(evidence[3]),
                )
            )
    session.flush()
    _refresh_search_vectors(session, identity.org_id)


@dataclass(frozen=True)
class MemorySpec:
    type: MemoryType
    title: str
    body: str
    status: MemoryStatus
    owner_id: UUID
    project_id: UUID | None
    visibility_scope: VisibilityScope
    source_tool: str
    tags: tuple[str, ...]
    rationale: str | None = None
    source_ref: str | None = None
    confidence: float | None = None
    source_context: JsonObject = field(default_factory=dict)
    evidence: tuple[tuple[EvidenceKind, str | None, str | None, JsonObject], ...] = ()


def _memory_specs(identity: SeededIdentity) -> list[MemorySpec]:
    project = identity.project_id
    pablo = identity.pablo_id
    fabio = identity.fabio_id
    payments_context: JsonObject = {
        "repository_url": "git@github.com:aircury/cecw.git",
        "branch": "fix/payment-sync-retries",
        "commit_sha": "abc123",
        "files": [
            {"path": "services/payment_sync/retry_handler.py", "line_start": 82, "line_end": 116}
        ],
    }
    return [
        MemorySpec(
            type=MemoryType.decision,
            title="Payment sync retries must use idempotency keys",
            body=(
                "Concurrent retries can process the same payment event more than once "
                "unless the retry path enforces idempotency."
            ),
            rationale="Found while debugging duplicate sync events in production.",
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="codex",
            source_ref="codex-thread-abc123",
            confidence=0.87,
            tags=("payments", "sync", "idempotency"),
            source_context=payments_context,
            evidence=(
                (
                    EvidenceKind.code_reference,
                    "Retry handler without idempotency",
                    "The retry handler processes events without an idempotency guard.",
                    {
                        "file_path": "services/payment_sync/retry_handler.py",
                        "line_start": 82,
                        "line_end": 116,
                    },
                ),
            ),
        ),
        MemorySpec(
            type=MemoryType.problem,
            title="Duplicate payment events during provider outages",
            body=(
                "When the payment provider times out, the webhook is redelivered and the "
                "sync job double-counts the settlement."
            ),
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="codex",
            tags=("payments", "webhooks"),
        ),
        MemorySpec(
            type=MemoryType.solution,
            title="Deduplicate settlements with a provider event ledger",
            body=(
                "Persist every provider event id in a ledger table and skip settlements "
                "whose event id already exists."
            ),
            rationale="Ledger lookups are cheap and make the sync job replay-safe.",
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="opencode",
            tags=("payments", "idempotency", "ledger"),
        ),
        MemorySpec(
            type=MemoryType.failed_attempt,
            title="Row locks on the settlements table caused deadlocks",
            body=(
                "Serialising the sync job with SELECT ... FOR UPDATE on settlements "
                "deadlocked under load. Abandoned in favour of the event ledger."
            ),
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="codex",
            tags=("payments", "database", "locking"),
        ),
        MemorySpec(
            type=MemoryType.procedure,
            title="How to replay a failed payment sync batch",
            body=(
                "1. Pause the sync worker. 2. Identify the batch id. 3. Re-run "
                "`nexus-payments replay --batch <id>`. 4. Verify the ledger counts."
            ),
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="manual",
            tags=("payments", "runbook"),
        ),
        MemorySpec(
            type=MemoryType.risk,
            title="Provider clock skew can reorder settlement events",
            body=(
                "The provider timestamps events with its own clock; skew above a few "
                "seconds can reorder events and mislead reconciliation."
            ),
            status=MemoryStatus.needs_review,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="codex",
            tags=("payments", "risk", "reconciliation"),
        ),
        MemorySpec(
            type=MemoryType.open_question,
            title="Should reconciliation run per-merchant or per-batch?",
            body=(
                "Per-merchant reconciliation isolates failures but multiplies job count. "
                "Undecided pending volume metrics."
            ),
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="manual",
            tags=("payments", "reconciliation"),
        ),
        MemorySpec(
            type=MemoryType.decision,
            title="Adopt keyset pagination for all list endpoints",
            body="List endpoints use opaque keyset cursors instead of offset pagination.",
            rationale="Offset pagination is unstable and slow under authorization filters.",
            status=MemoryStatus.pending_review,
            owner_id=fabio,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="codex",
            source_ref="codex-thread-def456",
            confidence=0.72,
            tags=("api", "pagination"),
        ),
        MemorySpec(
            type=MemoryType.problem,
            title="Search returns stale results after a memory is deprecated",
            body=(
                "Deprecated memory still appears in search until the search vector is "
                "refreshed on status change."
            ),
            status=MemoryStatus.pending_review,
            owner_id=fabio,
            project_id=project,
            visibility_scope=VisibilityScope.project,
            source_tool="opencode",
            tags=("search", "freshness"),
        ),
        MemorySpec(
            type=MemoryType.note,
            title="Personal note: CECW staging credentials rotate on Mondays",
            body="Staging tokens are rotated weekly; refresh the local .env before demos.",
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=None,
            visibility_scope=VisibilityScope.private,
            source_tool="manual",
            tags=("ops",),
        ),
        MemorySpec(
            type=MemoryType.task,
            title="Add reconciliation dashboard to the CECW ops page",
            body="Surface ledger drift and last successful sync time on the ops dashboard.",
            status=MemoryStatus.active,
            owner_id=pablo,
            project_id=project,
            visibility_scope=VisibilityScope.organization,
            source_tool="manual",
            tags=("dashboard", "ops"),
        ),
    ]


def _refresh_search_vectors(session: Session, org_id: UUID) -> None:
    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return
    session.execute(
        update(MemoryEntry)
        .where(MemoryEntry.org_id == org_id)
        .values(search_vector=postgres_search_vector())
    )


def _get_or_create[ModelT: object](
    session: Session,
    model: type[ModelT],
    match: dict[str, object],
    to_create: ModelT,
) -> ModelT:
    conditions = [getattr(model, key) == value for key, value in match.items()]
    existing = session.execute(select(model).where(*conditions)).scalar_one_or_none()
    if existing is not None:
        return existing
    session.add(to_create)
    return to_create


def _get_or_create_user(session: Session, org_id: UUID, email: str, display_name: str) -> User:
    existing = session.execute(
        select(User).where(User.org_id == org_id, User.email == email)
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    user = User(
        org_id=org_id,
        email=email,
        display_name=display_name,
        status=UserStatus.active,
    )
    session.add(user)
    return user


def _set_org_membership(
    session: Session, org_id: UUID, user_id: UUID, role: OrgRole, *, is_org_admin: bool
) -> None:
    membership = session.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id, OrgMembership.user_id == user_id
        )
    ).scalar_one_or_none()
    if membership is None:
        session.add(
            OrgMembership(org_id=org_id, user_id=user_id, role=role, is_org_admin=is_org_admin)
        )
        return
    membership.role = role
    membership.is_org_admin = is_org_admin


def _set_group_membership(
    session: Session, org_id: UUID, group_id: UUID, user_id: UUID, role: GroupRole
) -> None:
    membership = session.execute(
        select(GroupMembership).where(
            GroupMembership.org_id == org_id,
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        session.add(GroupMembership(org_id=org_id, group_id=group_id, user_id=user_id, role=role))
        return
    membership.role = role


def _set_project_membership(
    session: Session, org_id: UUID, project_id: UUID, user_id: UUID, role: ProjectRole
) -> None:
    membership = session.execute(
        select(ProjectMembership).where(
            ProjectMembership.org_id == org_id,
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if membership is None:
        session.add(
            ProjectMembership(org_id=org_id, project_id=project_id, user_id=user_id, role=role)
        )
        return
    membership.role = role


def _print_summary(session: Session, identity: SeededIdentity) -> None:
    memory_count = session.execute(
        select(func.count()).select_from(MemoryEntry).where(MemoryEntry.org_id == identity.org_id)
    ).scalar_one()
    print(f"Seeded organization '{ORG_SLUG}' (org_id={identity.org_id}).")
    print(f"Project '{PROJECT_KEY}' project_id={identity.project_id}.")
    print(f"Memory entries in org: {int(memory_count)}.")
    print(
        "Dev-login emails: pablo@aircury.com (maintainer/admin), fabio@aircury.com "
        "(contributor), carlos@aircury.com (viewer)."
    )


if __name__ == "__main__":
    seed()
