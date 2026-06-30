"""create initial nexus schema

Revision ID: 20260701_0001
Revises:
Create Date: 2026-07-01 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260701_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", name="organizations_slug_unique"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="users_org_id_fk"),
        sa.UniqueConstraint("org_id", "email", name="users_org_email_unique"),
        sa.UniqueConstraint("org_id", "id", name="users_org_id_unique"),
    )
    op.create_index("users_org_status_idx", "users", ["org_id", "status"])
    op.create_table(
        "org_memberships",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("is_org_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="org_memberships_org_id_fk"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="org_memberships_user_id_fk"),
        sa.UniqueConstraint("org_id", "user_id", name="org_memberships_org_user_unique"),
    )
    op.create_index("org_memberships_org_admin_idx", "org_memberships", ["org_id", "is_org_admin"])

    op.create_table(
        "groups",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("group_type", sa.Text(), nullable=False),
        sa.Column("parent_group_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="groups_org_id_fk"),
        sa.ForeignKeyConstraint(
            ["parent_group_id"], ["groups.id"], name="groups_parent_group_id_fk"
        ),
        sa.UniqueConstraint("org_id", "slug", name="groups_org_slug_unique"),
        sa.UniqueConstraint("org_id", "id", name="groups_org_id_unique"),
    )
    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], name="group_memberships_org_id_fk"
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name="group_memberships_group_id_fk"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="group_memberships_user_id_fk"),
        sa.UniqueConstraint("group_id", "user_id", name="group_memberships_group_user_unique"),
    )
    op.create_index("group_memberships_user_idx", "group_memberships", ["org_id", "user_id"])
    op.create_index("group_memberships_group_idx", "group_memberships", ["org_id", "group_id"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("owning_group_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="projects_org_id_fk"),
        sa.ForeignKeyConstraint(
            ["owning_group_id"], ["groups.id"], name="projects_owning_group_id_fk"
        ),
        sa.UniqueConstraint("org_id", "key", name="projects_org_key_unique"),
        sa.UniqueConstraint("org_id", "id", name="projects_org_id_unique"),
    )
    op.create_index("projects_org_group_idx", "projects", ["org_id", "owning_group_id"])
    op.create_table(
        "project_memberships",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], name="project_memberships_org_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="project_memberships_project_id_fk"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="project_memberships_user_id_fk"),
        sa.UniqueConstraint(
            "project_id", "user_id", name="project_memberships_project_user_unique"
        ),
    )
    op.create_index("project_memberships_user_idx", "project_memberships", ["org_id", "user_id"])
    op.create_index(
        "project_memberships_project_idx", "project_memberships", ["org_id", "project_id"]
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_subject", sa.Text(), nullable=False),
        sa.Column("client_type", sa.Text(), nullable=False),
        sa.Column("client_name", sa.Text(), nullable=True),
        sa.Column(
            "capabilities",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("max_visibility_scope", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="auth_sessions_org_id_fk"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="auth_sessions_user_id_fk"),
    )
    op.create_index("auth_sessions_org_id_unique", "auth_sessions", ["org_id", "id"], unique=True)
    op.create_index("auth_sessions_user_idx", "auth_sessions", ["org_id", "user_id"])
    op.create_index(
        "auth_sessions_provider_subject_idx",
        "auth_sessions",
        ["org_id", "provider", "provider_subject"],
    )
    op.create_index(
        "auth_sessions_lifecycle_idx", "auth_sessions", ["org_id", "revoked_at", "expires_at"]
    )

    op.create_table(
        "auth_cli_authorizations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("device_code_hash", sa.Text(), nullable=False),
        sa.Column("user_code_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "requested_capabilities",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("max_visibility_scope", sa.Text(), nullable=True),
        sa.Column("client_name", sa.Text(), nullable=False),
        sa.Column("approved_session_id", sa.Uuid(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exchanged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], name="auth_cli_authorizations_org_id_fk"
        ),
    )
    op.create_index(
        "auth_cli_authorizations_device_code_hash_unique",
        "auth_cli_authorizations",
        ["device_code_hash"],
        unique=True,
    )
    op.create_index(
        "auth_cli_authorizations_user_code_hash_unique",
        "auth_cli_authorizations",
        ["user_code_hash"],
        unique=True,
    )
    op.create_index(
        "auth_cli_authorizations_status_expires_idx",
        "auth_cli_authorizations",
        ["status", "expires_at"],
    )
    op.create_index(
        "auth_cli_authorizations_user_idx", "auth_cli_authorizations", ["org_id", "user_id"]
    )

    op.create_table(
        "auth_refresh_tokens",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("parent_token_id", sa.Uuid(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], name="auth_refresh_tokens_org_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["auth_sessions.id"], name="auth_refresh_tokens_session_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["parent_token_id"],
            ["auth_refresh_tokens.id"],
            name="auth_refresh_tokens_parent_token_id_fk",
        ),
    )
    op.create_index(
        "auth_refresh_tokens_token_hash_unique", "auth_refresh_tokens", ["token_hash"], unique=True
    )
    op.create_index(
        "auth_refresh_tokens_session_idx", "auth_refresh_tokens", ["org_id", "session_id"]
    )

    op.create_table(
        "memory_entries",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("submitted_via_session_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("visibility_scope", sa.Text(), nullable=False),
        sa.Column("visibility_group_id", sa.Uuid(), nullable=True),
        sa.Column("source_kind", sa.Text(), nullable=False),
        sa.Column("source_tool", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("client_entry_id", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "source_context",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "confidence is null or (confidence >= 0 and confidence <= 1)",
            name="memory_entries_confidence_range",
        ),
        sa.CheckConstraint(
            "(visibility_scope = 'group' and visibility_group_id is not null) or "
            "(visibility_scope != 'group' and visibility_group_id is null)",
            name="memory_entries_group_visibility_shape",
        ),
        sa.CheckConstraint(
            "visibility_scope != 'project' or project_id is not null",
            name="memory_entries_project_visibility_requires_project",
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="memory_entries_org_id_fk"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name="memory_entries_project_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"], ["users.id"], name="memory_entries_owner_user_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], name="memory_entries_created_by_user_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["submitted_via_session_id"],
            ["auth_sessions.id"],
            name="memory_entries_submitted_via_session_id_fk",
        ),
        sa.ForeignKeyConstraint(
            ["visibility_group_id"], ["groups.id"], name="memory_entries_visibility_group_id_fk"
        ),
    )
    op.create_index("memory_entries_org_id_unique", "memory_entries", ["org_id", "id"], unique=True)
    op.create_index("memory_entries_org_project_idx", "memory_entries", ["org_id", "project_id"])
    op.create_index("memory_entries_status_idx", "memory_entries", ["org_id", "status"])
    op.create_index(
        "memory_entries_visibility_idx", "memory_entries", ["org_id", "visibility_scope"]
    )
    op.create_index("memory_entries_owner_idx", "memory_entries", ["org_id", "owner_user_id"])
    op.create_index(
        "memory_entries_group_visibility_idx", "memory_entries", ["org_id", "visibility_group_id"]
    )
    op.create_index(
        "memory_entries_source_ref_idx", "memory_entries", ["org_id", "source_tool", "source_ref"]
    )
    op.create_index(
        "memory_entries_client_entry_id_unique",
        "memory_entries",
        ["org_id", "created_by_user_id", "source_tool", "client_entry_id"],
        unique=True,
    )

    op.create_table(
        "memory_entry_grants",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("memory_entry_id", sa.Uuid(), nullable=False),
        sa.Column("grantee_user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], name="memory_entry_grants_org_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["memory_entry_id"],
            ["memory_entries.id"],
            name="memory_entry_grants_memory_entry_id_fk",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["grantee_user_id"], ["users.id"], name="memory_entry_grants_grantee_user_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], name="memory_entry_grants_created_by_user_id_fk"
        ),
    )
    op.create_index(
        "memory_entry_grants_entry_grantee_unique",
        "memory_entry_grants",
        ["memory_entry_id", "grantee_user_id"],
        unique=True,
    )
    op.create_index(
        "memory_entry_grants_grantee_idx", "memory_entry_grants", ["org_id", "grantee_user_id"]
    )

    op.create_table(
        "memory_entry_evidence",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("memory_entry_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column(
            "locator",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], name="memory_entry_evidence_org_id_fk"
        ),
        sa.ForeignKeyConstraint(
            ["memory_entry_id"],
            ["memory_entries.id"],
            name="memory_entry_evidence_memory_entry_id_fk",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "memory_entry_evidence_entry_idx", "memory_entry_evidence", ["org_id", "memory_entry_id"]
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_session_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="audit_events_org_id_fk"),
    )
    op.create_index("audit_events_org_created_idx", "audit_events", ["org_id", "created_at"])
    op.create_index(
        "audit_events_resource_idx", "audit_events", ["org_id", "resource_type", "resource_id"]
    )


def downgrade() -> None:
    for table_name in [
        "audit_events",
        "memory_entry_evidence",
        "memory_entry_grants",
        "memory_entries",
        "auth_refresh_tokens",
        "auth_cli_authorizations",
        "auth_sessions",
        "project_memberships",
        "projects",
        "group_memberships",
        "groups",
        "org_memberships",
        "users",
        "organizations",
    ]:
        op.drop_table(table_name)
