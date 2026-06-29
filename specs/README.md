# Nexus Spec Index

This directory is the canonical specification source for Nexus. It contains product, domain, data, security, API, search, implementation, technical-standard, and behavior specs used for spec-driven development.

## Source Hierarchy

| Priority | Source | Use |
| --- | --- | --- |
| 1 | ADRs in `docs/adr` | Binding architectural decisions. |
| 2 | Specs in `specs/` | Binding product, domain, API, security, data, implementation, and engineering-standard requirements. |
| 3 | Gherkin in `specs/features` | Binding behavior and acceptance scenarios. |
| 4 | Traceability in `specs/traceability` | Coverage proof and mapping from decomposed source material. |
| 5 | `AGENTS.md` | Operational entry point for coding agents; points to binding specs. |

If sources conflict, update the relevant spec and add or amend an ADR. Do not silently implement behavior that contradicts an ADR or a feature scenario.

## Implementation Reading Order

| Step | Read |
| --- | --- |
| 1 | `product/overview.md` |
| 2 | `domain/model.md` |
| 3 | `security/authorization.md` |
| 4 | `data/schema.dbml` |
| 5 | `implementation/repository-structure.md` |
| 6 | `implementation/python-style.md` |
| 7 | `implementation/code-quality.md` |
| 8 | `implementation/internal-services.md` |
| 9 | `api/rest-api.md` |
| 10 | `search/search-and-context-packs.md` |
| 11 | `security/security-observability-audit.md` |
| 12 | `implementation/testing.md` |
| 13 | Relevant `features/*.feature` files |
| 14 | Relevant `docs/adr/*.md` files |

## Spec Files

| File | Contents |
| --- | --- |
| `product/overview.md` | Product problem, goals, non-goals, workflows, and acceptance criteria. |
| `product/roadmap.md` | Delivery phases, future extensions, and risk mitigations. |
| `product/ui-cli.md` | Minimal UI views and CLI/plugin responsibilities. |
| `domain/model.md` | Entities, relationships, roles, memory types, statuses, visibility, source context. |
| `data/schema.dbml` | Physical database model in DBML including tables, enums, relationships, and indexes. |
| `security/authorization.md` | Actor model, auth session model, role derivation, read/create/review/update rules. |
| `security/security-observability-audit.md` | Security controls, audit events, logs, metrics, and privacy rules. |
| `api/rest-api.md` | REST endpoints, payload examples, default behavior, audit expectations. |
| `search/search-and-context-packs.md` | Full text search, ranking, safe filtering, context packs, project timeline. |
| `implementation/repository-structure.md` | Required FastAPI/Python repository structure and module layout. |
| `implementation/internal-services.md` | Auth, authorization, memory, search, context pack, and audit service responsibilities. |
| `implementation/testing.md` | Required test classes and invariant list. |
| `implementation/spec-driven-development.md` | Process for keeping code, tests, specs, and ADRs aligned. |
| `implementation/code-quality.md` | Ruff, basedpyright, pytest, coverage, and suppression policy. |
| `implementation/python-style.md` | Python naming, imports, typing, FastAPI, Pydantic, SQLAlchemy, logging, and service style. |
| `implementation/ci-quality-gates.md` | Required CI checks and coverage thresholds. |
| `implementation/dependency-management.md` | Dependency tooling, groups, versioning, and package acceptance rules. |
| `implementation/database-migrations.md` | DBML/Alembic migration contract and review checklist. |
| `implementation/agent-workflow.md` | Canonical workflow for coding agents. |
| `implementation/open-questions.md` | Resolved implementation decisions and future open gaps. |
| `implementation/ai-implementation-prompt.md` | Prompt for coding agents. |
| `traceability/project-brief-coverage.md` | Coverage map for the decomposed source brief. |

## Feature Files

| File | Behavior area |
| --- | --- |
| `features/auth_and_sessions.feature` | Authentication, session capabilities, refresh rotation, session limits. |
| `features/effective_project_roles.feature` | Project role derivation and precedence. |
| `features/memory_creation_and_review.feature` | Creation, initial status, review, state transitions. |
| `features/memory_read_authorization.feature` | Read authorization by visibility scope and status. |
| `features/visibility_and_grants.feature` | Restricted grants and visibility changes. |
| `features/search.feature` | Authorized full text search behavior. |
| `features/context_packs.feature` | Context pack grouping, limits, warnings, exclusions. |
| `features/audit.feature` | Audit events and sensitive metadata handling. |
| `features/api_contracts.feature` | Endpoint-level contracts, idempotency, bulk, timeline. |
| `features/ui_and_cli.feature` | Minimal UI and CLI/plugin behavior. |

## Maintenance Rules

| Rule | Requirement |
| --- | --- |
| Spec-first changes | Change specs before code when behavior changes. |
| Tests follow Gherkin | Each behavior scenario should map to at least one automated test. |
| ADRs for tradeoffs | Architecture, security, storage, auth, or long-lived process decisions need ADRs. |
| No implicit permissions | Any new read path must reuse the shared readable memory query. |
| No hidden AI dependency | The API must not call LLMs in product behavior. |
| Open questions stay visible | Do not fill gaps by assumption; document or decide them. |
| Technical standards are binding | Code must follow implementation specs, not just product behavior specs. |
| Quality gates are mandatory | Python changes must satisfy Ruff, basedpyright, pytest, and coverage gates. |

## Traceability Labels

Use these labels in issues, PRs, commits, or test names when possible:

| Label | Meaning |
| --- | --- |
| `SPEC-PRODUCT` | Product behavior or acceptance criteria. |
| `SPEC-DOMAIN` | Entity, enum, state, or relationship behavior. |
| `SPEC-AUTHZ` | Permission, auth session, role, or visibility behavior. |
| `SPEC-API` | Endpoint contract behavior. |
| `SPEC-SEARCH` | Search, ranking, or context pack behavior. |
| `SPEC-AUDIT` | Audit, logging, observability, or security behavior. |
| `SPEC-IMPL` | Repository structure, code quality, CI, dependencies, migrations, or agent workflow. |
| `ADR` | Architectural decision. |
| `GHERKIN` | Scenario-backed behavior. |
