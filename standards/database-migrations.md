# Database Migrations Spec

## Purpose

The DBML schema defines intended data shape. Alembic migrations implement that shape over time. The two must not drift.

## Source Of Truth

| Artifact | Role |
| --- | --- |
| `specs/data/schema.dbml` | Canonical intended schema. |
| Alembic migrations | Executable history to reach the intended schema. |
| SQLAlchemy models | Runtime mapping that must match DBML and migrations. |

When schema behavior changes, update DBML first, then migration, then SQLAlchemy models/tests.

## Migration Location

Alembic files live under:

```text
app/db/migrations/
  env.py
  script.py.mako
  versions/
```

Migration versions are operational code. They must be readable and pass Ruff, but may be excluded from strict basedpyright if generated Alembic patterns are too noisy.

## Naming

Migration messages should be short and behavior-oriented:

```text
create_identity_tables
add_memory_review_fields
add_auth_sessions
```

Do not use vague names such as `update_schema` or `fix`.

## Required Migration Practices

| Rule | Requirement |
| --- | --- |
| Tenant isolation | Tenant-owned tables include `org_id`. |
| Cross-org safety | Use composite foreign keys where practical. |
| Naming | Name constraints and indexes explicitly. |
| Nullability | Prefer `not null` where the domain requires a value. |
| Defaults | Use server-side defaults for timestamps and generated IDs. |
| Reversibility | Provide `downgrade()` when safe. If not safe, document why. |
| Data migrations | Keep data migrations deterministic, idempotent when possible, and audited in review. |
| Transactions | Prefer transactional DDL/data changes where PostgreSQL supports them. |

## Constraints And Indexes

Migrations must enforce domain invariants from specs when PostgreSQL can enforce them:

| Invariant | Enforcement |
| --- | --- |
| `confidence` range | Check `confidence is null or confidence between 0 and 1`. |
| Group visibility | Check `visibility_group_id` exists only for `group` visibility. |
| Project visibility | Check `project_id` exists for `project` visibility. |
| One grant per user/memory | Unique index on memory/grantee pair. |
| Client idempotency | Partial unique index for non-null `client_entry_id`. |
| Search | GIN index for PostgreSQL FTS vector. |

## Review Checklist

Every migration review should verify:

| Check | Required outcome |
| --- | --- |
| DBML updated | `specs/data/schema.dbml` reflects the migration. |
| Models updated | SQLAlchemy models match migration. |
| Tests updated | Tests cover new constraint, relationship, or state behavior. |
| Downgrade considered | Downgrade is implemented or non-reversibility is explained. |
| Large table risk | Backfills/indexes consider lock and runtime impact. |
| Security | No migration weakens tenant isolation or read authorization. |

## Forbidden Practices

| Practice | Reason |
| --- | --- |
| Importing app models in migrations | Models drift over time and break historical migrations. |
| Silent destructive changes | Data loss requires explicit spec/ADR and migration notes. |
| SQLite-only assumptions | Product uses PostgreSQL semantics. |
| Unnamed constraints/indexes | Harder to diff, debug, and migrate. |
