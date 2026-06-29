# AGENTS.md

## Project Overview

Nexus is a governed shared memory API for AI-assisted teams. It stores structured memory entries, enforces tenant-aware authorization, supports review workflows, provides authorized search/context packs, and keeps audit trails.

The repository is spec-first. Code is an implementation detail and should be rebuildable from `docs/adr`, `specs/`, `standards/`, DBML, and Gherkin features.

## Source Of Truth

Read sources in this order when there is a conflict:

| Priority | Source | Role |
| --- | --- | --- |
| 1 | `docs/adr/*.md` | Binding architectural decisions. |
| 2 | `specs/**/*.md` and `specs/data/schema.dbml` | Product, API, security, data, and behavior contracts. |
| 3 | `standards/**/*.md` | Engineering, implementation, quality, and workflow contracts. |
| 4 | `specs/features/*.feature` | Acceptance behavior. |
| 5 | `AGENTS.md` | Operational instructions for agents. |

Do not implement behavior or technical design that contradicts ADRs, specs, standards, DBML, or Gherkin. Update the relevant source first.

## Required Reading

For any non-trivial task, start with:

```text
specs/README.md
standards/README.md
standards/spec-driven-development.md
standards/agent-workflow.md
```

For Python implementation tasks, also read:

```text
standards/backend/repository-structure.md
standards/python/style.md
standards/python/code-quality.md
standards/ci-quality-gates.md
```

For data/schema tasks, read:

```text
specs/data/schema.dbml
standards/database-migrations.md
specs/domain/model.md
```

For auth, permissions, memory visibility, search, context packs, or audit, read the matching security/API/search specs before editing code.

## Non-Negotiable Rules

| Rule | Requirement |
| --- | --- |
| Spec first | Behavior, data, architecture, or technical-standard changes update specs/ADRs/Gherkin before code. |
| No invented behavior | If unspecified, ask or update `docs/decisions/resolved-questions.md`. |
| No authorization bypass | Every memory read path must use shared readable/reviewable memory logic. |
| No direct client DB/index access | All clients use the API. |
| No API-side LLM | The API does not call LLMs or generate embeddings in v1. |
| No generic runtime utilities | Follow `repository-structure.md`; do not create vague `utils.py` or `helpers.py` in app code. |
| No broad suppressions | Do not add broad Ruff or basedpyright ignores. |
| No secret leakage | Never commit or log secrets, access tokens, refresh tokens, authorization codes, raw search queries, or full secret-bearing bodies. |

## Python Structure

The runtime app must follow `standards/backend/repository-structure.md`.

Core direction:

```text
router -> service -> repository -> models
service -> authorization/audit/other services through explicit dependencies
common -> no product modules
```

Routers are thin. Services own business workflows, transactions, authorization calls, and audit orchestration. Repositories encapsulate persistence and never commit independently.

## Quality Commands

When Python code exists, run these from the repository root before claiming completion:

```sh
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest
uv run coverage run -m pytest
uv run coverage report
```

Ruff passing is not enough. basedpyright must also pass. Zed diagnostics should match `pyrightconfig.json` and CI.

If a command cannot be run, report it explicitly with the reason.

## Dependency Rules

Use `uv`, `pyproject.toml`, and `uv.lock`. Do not add dependencies casually. Prefer the standard library for simple needs, prefer typed packages, and keep provider SDKs behind module adapters.

Dependency changes must update both `pyproject.toml` and `uv.lock`.

## Testing Rules

Tests are behavior-first and should map to specs or Gherkin scenarios.

Required test guidance lives in:

```text
standards/testing.md
specs/features/*.feature
```

Authorization, tenant isolation, search safety, context pack safety, audit, auth sessions, admin boundaries, error envelopes, and pagination are product-critical.

## Database Rules

DBML is the intended schema. Alembic migrations implement it over time.

Schema changes must update:

```text
specs/data/schema.dbml
app/db/migrations/versions/*
SQLAlchemy models
tests
```

Follow `standards/database-migrations.md`. Use PostgreSQL semantics, named constraints/indexes, tenant-safe composite foreign keys where practical, and explicit migration review.

## Commit Rules

Only commit when explicitly asked.

Before committing, inspect:

```sh
git status --short
git diff
git diff --staged
git log --oneline -10
```

Commit atomically by functional intent. Use Conventional Commits such as `docs:`, `feat:`, `fix:`, `test:`, `refactor:`, `chore:`. Do not add AI tool credits or co-author trailers.

## Completion Report

When finishing work, report:

| Item | Requirement |
| --- | --- |
| Changes | Concise list of important specs/code changed. |
| Verification | Commands run and results. |
| Not run | Any skipped check and why. |
| Remaining work | Only real follow-ups or blockers. |
