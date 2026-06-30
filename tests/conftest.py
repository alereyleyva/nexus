from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, load_all_models
from app.modules.auth.models import AuthClientType
from app.modules.auth.types import ActorContext
from app.modules.groups.models import Group, GroupMembership, GroupRole, GroupType
from app.modules.identity.models import Organization, OrgMembership, OrgRole, User, UserStatus
from app.modules.memory_entries.models import MemoryType, SourceKind, VisibilityScope
from app.modules.memory_entries.schemas import CreateMemoryEntryRequest
from app.modules.projects.models import Project, ProjectMembership, ProjectRole, ProjectStatus


@dataclass(frozen=True)
class SeedData:
    org: Organization
    other_org: Organization
    pablo: User
    fabio: User
    carlos: User
    group: Group
    other_group: Group
    project: Project


@pytest.fixture
def db() -> Generator[Session]:
    load_all_models()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def seed(db: Session) -> SeedData:
    org = Organization(slug="aircury", name="Aircury")
    other_org = Organization(slug="other-org", name="Other Org")
    db.add_all([org, other_org])
    db.flush()
    pablo = User(
        org_id=org.id,
        email="pablo@example.com",
        display_name="Pablo",
        status=UserStatus.active,
    )
    fabio = User(
        org_id=org.id,
        email="fabio@example.com",
        display_name="Fabio",
        status=UserStatus.active,
    )
    carlos = User(
        org_id=org.id,
        email="carlos@example.com",
        display_name="Carlos",
        status=UserStatus.active,
    )
    db.add_all([pablo, fabio, carlos])
    db.flush()
    db.add_all(
        [
            OrgMembership(org_id=org.id, user_id=pablo.id, role=OrgRole.member, is_org_admin=False),
            OrgMembership(org_id=org.id, user_id=fabio.id, role=OrgRole.member, is_org_admin=False),
            OrgMembership(
                org_id=org.id, user_id=carlos.id, role=OrgRole.member, is_org_admin=False
            ),
        ]
    )
    group = Group(org_id=org.id, slug="backend", name="Backend Team", group_type=GroupType.team)
    other_group = Group(org_id=org.id, slug="ai", name="AI Team", group_type=GroupType.team)
    db.add_all([group, other_group])
    db.flush()
    project = Project(
        org_id=org.id,
        owning_group_id=group.id,
        key="CECW",
        name="CECW",
        status=ProjectStatus.active,
    )
    db.add(project)
    db.commit()
    return SeedData(
        org=org,
        other_org=other_org,
        pablo=pablo,
        fabio=fabio,
        carlos=carlos,
        group=group,
        other_group=other_group,
        project=project,
    )


def actor(
    *,
    org_id: UUID,
    user_id: UUID,
    capabilities: set[str] | None = None,
    max_visibility_scope: VisibilityScope | None = None,
    request_id: str = "test-request",
) -> ActorContext:
    return ActorContext(
        org_id=org_id,
        user_id=user_id,
        session_id=uuid4(),
        session_capabilities=capabilities or set(),
        session_max_visibility_scope=max_visibility_scope,
        client_type=AuthClientType.web.value,
        request_id=request_id,
    )


def memory_request(
    *,
    visibility_scope: VisibilityScope | None = None,
    project_id: UUID | None = None,
    visibility_group_id: UUID | None = None,
    title: str = "Payment sync retries must use idempotency keys",
    body: str = "Concurrent retries can duplicate payment events.",
    tags: list[str] | None = None,
) -> CreateMemoryEntryRequest:
    return CreateMemoryEntryRequest(
        project_id=project_id,
        type=MemoryType.decision,
        title=title,
        body=body,
        rationale="The retry path can execute twice.",
        visibility_scope=visibility_scope,
        visibility_group_id=visibility_group_id,
        source_kind=SourceKind.ai_cli,
        source_tool="codex",
        client_entry_id=None,
        tags=tags or ["payments", "sync"],
    )


def add_group_membership(
    db: Session, *, org_id: UUID, group_id: UUID, user_id: UUID, role: GroupRole
) -> None:
    db.add(GroupMembership(org_id=org_id, group_id=group_id, user_id=user_id, role=role))
    db.commit()


def add_project_membership(
    db: Session, *, org_id: UUID, project_id: UUID, user_id: UUID, role: ProjectRole
) -> None:
    db.add(ProjectMembership(org_id=org_id, project_id=project_id, user_id=user_id, role=role))
    db.commit()
