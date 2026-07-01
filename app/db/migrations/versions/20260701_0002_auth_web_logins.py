"""create auth_web_logins for OIDC web login handoff

Revision ID: 20260701_0002
Revises: 20260701_0001
Create Date: 2026-07-01 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0002"
down_revision: str | None = "20260701_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_web_logins",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("login_code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], name="auth_web_logins_org_id_fk"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="auth_web_logins_user_id_fk"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["auth_sessions.id"], name="auth_web_logins_session_id_fk"
        ),
    )
    op.create_index(
        "auth_web_logins_login_code_hash_unique",
        "auth_web_logins",
        ["login_code_hash"],
        unique=True,
    )
    op.create_index("auth_web_logins_session_idx", "auth_web_logins", ["org_id", "session_id"])


def downgrade() -> None:
    op.drop_index("auth_web_logins_session_idx", table_name="auth_web_logins")
    op.drop_index("auth_web_logins_login_code_hash_unique", table_name="auth_web_logins")
    op.drop_table("auth_web_logins")
