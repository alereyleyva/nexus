# Engineering Standards Index

This directory contains the binding engineering standards for Nexus. These files define how implementation work must be structured, typed, tested, linted, migrated, and operated by coding agents.

Product behavior lives under `specs/`. Engineering standards live here.

## Standards Files

| File | Contents |
| --- | --- |
| `spec-driven-development.md` | Process for keeping specs, ADRs, tests, and code aligned. |
| `agent-workflow.md` | Canonical workflow for coding agents. |
| `backend/repository-structure.md` | Required FastAPI/Python repository and module layout. |
| `backend/internal-services.md` | Internal service responsibilities and function boundaries. |
| `backend/implementation-templates.md` | Deterministic sync FastAPI/SQLAlchemy module templates and layer skeletons. |
| `backend/error-audit-patterns.md` | Project exception, Problem Details, and audit persistence implementation pattern. |
| `python/style.md` | Python naming, imports, typing, FastAPI, Pydantic, SQLAlchemy, logging, and service style. |
| `python/code-quality.md` | Ruff, basedpyright, pytest, coverage, and suppression policy. |
| `testing.md` | Required test classes and invariant list. |
| `ci-quality-gates.md` | Required CI checks and coverage thresholds. |
| `dependency-management.md` | Dependency tooling, groups, versioning, and package acceptance rules. |
| `database-migrations.md` | DBML/Alembic migration contract and review checklist. |
| `ai-implementation-prompt.md` | Prompt for coding agents. |

## Required Reading

For Python implementation tasks, read:

```text
standards/spec-driven-development.md
standards/agent-workflow.md
standards/backend/repository-structure.md
standards/backend/internal-services.md
standards/python/style.md
standards/python/code-quality.md
standards/backend/implementation-templates.md
standards/backend/error-audit-patterns.md
```

For database tasks, also read:

```text
standards/database-migrations.md
specs/data/schema.dbml
```

For dependency or CI/tooling tasks, read:

```text
standards/dependency-management.md
standards/ci-quality-gates.md
```

## Maintenance Rules

| Rule | Requirement |
| --- | --- |
| Standards are binding | Code must follow these standards unless an ADR changes them. |
| Keep product separate | Do not put product behavior contracts in `standards/`; use `specs/`. |
| Keep standards practical | Standards should be strict enough to prevent drift and concise enough to apply. |
| Update AGENTS | If workflow expectations change, update `AGENTS.md`. |
