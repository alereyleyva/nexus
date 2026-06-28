# Project Brief Coverage

This file records how the original monolithic project brief was decomposed into canonical specs. The original brief is no longer required as a source file because every durable requirement has a maintained destination below.

## Coverage Map

| Original area | Canonical destination |
| --- | --- |
| Document control, executive summary, product one-liner, problem statement, inspiration | `specs/product/overview.md`, `README.md` |
| Product goals, business goals, technical goals | `specs/product/overview.md` |
| Explicit non-goals and avoided complexity | `specs/product/overview.md`, `docs/adr/0002-memory-entries-not-sessions.md`, `docs/adr/0003-users-not-ai-tools-are-permission-actors.md`, `docs/adr/0008-no-llm-or-embeddings-in-api.md` |
| Design principles: memory over sessions, users as actors, API-only access, PostgreSQL source of truth, context/visibility separation, private by default, human review, simple extensible architecture | `specs/product/overview.md`, `specs/security/authorization.md`, `docs/adr/0002-memory-entries-not-sessions.md`, `docs/adr/0003-users-not-ai-tools-are-permission-actors.md`, `docs/adr/0004-postgresql-source-of-truth.md`, `docs/adr/0005-separate-context-from-visibility.md`, `docs/adr/0006-human-review-for-shared-memory.md` |
| Conceptual domain model and organization/group/project relationships | `specs/domain/model.md`, `docs/adr/0009-projects-owned-by-groups.md` |
| Domain entities: organizations, users, memberships, groups, projects, auth sessions, refresh tokens, memory entries, evidence, grants, audit events | `specs/domain/model.md`, `specs/data/schema.dbml` |
| Memory types, examples, expected rationale/body semantics | `specs/domain/model.md`, `specs/features/memory_creation_and_review.feature` |
| Memory statuses, visible/hidden status behavior, state transitions | `specs/domain/model.md`, `specs/security/authorization.md`, `specs/features/memory_creation_and_review.feature`, `specs/features/memory_read_authorization.feature` |
| Visibility scopes and audience rules | `specs/domain/model.md`, `specs/security/authorization.md`, `specs/features/memory_read_authorization.feature`, `specs/features/visibility_and_grants.feature` |
| Effective project roles and derivation from owning group | `specs/domain/model.md`, `specs/security/authorization.md`, `specs/features/effective_project_roles.feature`, `docs/adr/0009-projects-owned-by-groups.md` |
| Read authorization query and shared readable memory rule | `specs/security/authorization.md`, `specs/features/memory_read_authorization.feature`, `specs/features/search.feature`, `specs/features/context_packs.feature` |
| Create, edit, approve, review, and visibility-change permissions | `specs/security/authorization.md`, `specs/features/memory_creation_and_review.feature`, `specs/features/visibility_and_grants.feature` |
| Authentication, OIDC login, session capabilities, refresh rotation, max visibility, session behavior | `specs/security/authorization.md`, `specs/api/rest-api.md`, `specs/features/auth_and_sessions.feature`, `docs/adr/0010-oidc-short-lived-user-sessions.md` |
| PostgreSQL requirements, tables, constraints, relationships, indexes, idempotency | `specs/data/schema.dbml` |
| Search behavior, PostgreSQL full text search, search vector, ranking, filters, secure search | `specs/search/search-and-context-packs.md`, `specs/features/search.feature`, `docs/adr/0007-postgresql-full-text-search-first.md` |
| Context packs, grouping, warnings, exclusions, AI client usage | `specs/search/search-and-context-packs.md`, `specs/features/context_packs.feature`, `docs/adr/0008-no-llm-or-embeddings-in-api.md` |
| REST API endpoints, request/response examples, idempotency, bulk create, review, grants, timeline | `specs/api/rest-api.md`, `specs/features/api_contracts.feature` |
| Source context examples for code, meetings, documents, support | `specs/domain/model.md`, `specs/api/rest-api.md`, `specs/features/api_contracts.feature` |
| Audit events, audit metadata, search audit safety | `specs/security/security-observability-audit.md`, `specs/features/audit.feature` |
| Security and privacy controls, future embedding risks | `specs/security/security-observability-audit.md`, `docs/adr/0004-postgresql-source-of-truth.md`, `docs/adr/0007-postgresql-full-text-search-first.md` |
| Technical architecture, stack, repository layout, module structure | `specs/implementation/repository-structure.md`, `specs/implementation/internal-services.md`, `docs/adr/0001-modular-monolith-api-first.md` |
| Internal service responsibilities: auth, authorization, memory, search, context packs, audit | `specs/implementation/internal-services.md` |
| Main workflows: private memory, project proposals, reviewer-created memory, handover, restricted sharing | `specs/product/overview.md`, `specs/features/memory_creation_and_review.feature`, `specs/features/context_packs.feature`, `specs/features/visibility_and_grants.feature` |
| Minimal UI and CLI/plugin contract | `specs/product/ui-cli.md`, `specs/features/ui_and_cli.feature` |
| Mandatory testing, invariants, search/context/audit tests | `specs/implementation/testing.md`, `specs/features/*.feature` |
| Observability, logs, technical metrics, product metrics | `specs/security/security-observability-audit.md` |
| Roadmap, future extensions, risks and mitigations | `specs/product/roadmap.md` |
| Acceptance criteria | `specs/product/overview.md`, `specs/implementation/testing.md`, `specs/features/*.feature` |
| AI implementation prompt | `specs/implementation/ai-implementation-prompt.md` |
| Final product framing and conclusion | `README.md`, `specs/product/overview.md` |

## Decomposition Decision

The original project brief was useful as an input document, but it mixed product goals, architecture, API contracts, database schema, behavior specs, implementation guidance, roadmap, and prompt material in one long file. The maintained sources are now split by responsibility:

| Responsibility | Maintained source |
| --- | --- |
| Product truth | `specs/product/overview.md` |
| Domain truth | `specs/domain/model.md` |
| Data truth | `specs/data/schema.dbml` |
| Authorization and security truth | `specs/security/*.md` |
| API truth | `specs/api/rest-api.md` |
| Search/context truth | `specs/search/search-and-context-packs.md` |
| Behavior truth | `specs/features/*.feature` |
| Implementation guidance | `specs/implementation/*.md` |
| Architecture decisions | `docs/adr/*.md` |

Future changes should update the maintained source directly. Do not recreate a monolithic project brief.
