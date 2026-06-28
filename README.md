# Nexus

Nexus is a governed shared memory layer for organizations and projects that work with AI tools. Developers and teams can store reusable knowledge such as decisions, problems, solutions, failed attempts, procedures, risks, open questions, tasks, and notes.

The product is intentionally API-first and simple: AI tools submit structured memory entries on behalf of real users, the API validates identity and authorization, PostgreSQL persists the source of truth, and search/context packs return only authorized memory.

## Current Status

This repository contains the canonical product specifications for Nexus, organized for spec-driven implementation and maintenance.

## Spec Map

| File | Purpose |
| --- | --- |
| `specs/README.md` | Canonical index for spec-driven development. |
| `specs/product/overview.md` | Product goals, non-goals, scope, workflows, acceptance criteria. |
| `specs/product/roadmap.md` | Delivery phases, future extensions, risks, and mitigations. |
| `specs/product/ui-cli.md` | Minimal UI and CLI/plugin contracts. |
| `specs/domain/model.md` | Domain entities, relationships, enums, states, visibility model. |
| `specs/data/schema.dbml` | Database model in DBML. |
| `specs/security/authorization.md` | Roles, effective permissions, auth session limits, read/write/review rules. |
| `specs/security/security-observability-audit.md` | Security, privacy, audit, logs, and metrics. |
| `specs/api/rest-api.md` | REST endpoints and request/response contracts. |
| `specs/search/search-and-context-packs.md` | PostgreSQL FTS search and context pack behavior. |
| `specs/implementation/internal-services.md` | Internal service responsibilities and function boundaries. |
| `specs/implementation/repository-structure.md` | Recommended FastAPI repository layout. |
| `specs/implementation/testing.md` | Mandatory test coverage and invariants. |
| `specs/implementation/spec-driven-development.md` | Rules for maintaining the project from specs. |
| `specs/implementation/open-questions.md` | Resolved implementation decisions and any future open gaps. |
| `specs/implementation/ai-implementation-prompt.md` | Implementation prompt for an AI coding agent. |
| `specs/features/*.feature` | Behavior specs in Gherkin. |
| `specs/traceability/project-brief-coverage.md` | Coverage map proving the original brief was decomposed into specs. |
| `docs/adr/*.md` | Architectural Decision Records. |

## Product Principles

| Principle | Requirement |
| --- | --- |
| Memory entry is the primary unit | Do not require AI/source sessions, messages, repositories, or batches as memory resources. |
| Users are permission actors | AI tools act on behalf of users and are recorded as source tools. |
| API is the only entry point | No client may access PostgreSQL, vector stores, or search indexes directly. |
| PostgreSQL is source of truth | Future vector stores are derived indexes only. |
| Context and visibility are separate | A memory can reference a project without being visible to the project. |
| Private by default | Missing visibility means `private`. |
| Shared memory is governed | Group, project, and organization memory may require review. |
| No LLM in the API | AI happens in clients/tools, not inside the API. |

## Recommended Stack

| Layer | Technology |
| --- | --- |
| Runtime | Python 3.12 |
| API | FastAPI |
| Schemas | Pydantic v2 |
| ORM | SQLAlchemy 2 |
| Migrations | Alembic |
| Database | PostgreSQL 16+ |
| Tests | pytest |
| Linting | ruff |
| Typing | mypy |
| Local infra | docker-compose |

## Implementation Modules

| Module | Responsibility |
| --- | --- |
| `identity` | Organizations, users, and org memberships. |
| `auth` | OIDC login, CLI browser SSO, auth sessions, access JWT validation, refresh rotation. |
| `admin` | Organization users, roles, groups, projects, and memberships. |
| `groups` | Groups, teams, and memberships. |
| `projects` | Projects, ownership, memberships, and timeline. |
| `authorization` | Effective roles, policies, and readable memory query. |
| `memory_entries` | Memory CRUD, evidence, grants, review, visibility changes. |
| `search` | PostgreSQL full text search over authorized memory. |
| `context_packs` | Structured authorized memory packs for tasks and handovers. |
| `audit` | Audit events for sensitive actions and denials. |

## Definition Of Done

The product is functional when:

| Capability | Expected result |
| --- | --- |
| Private memory | A user can create and read their own private memory. |
| Project proposals | A contributor can propose project memory and it becomes `pending_review`. |
| Review | A reviewer or maintainer can approve project memory. |
| Authorization | Search, context packs, timeline, and detail reads use the same readable memory query. |
| Isolation | Users cannot read memory from other organizations or unauthorized scopes. |
| Grants | Restricted memory can be shared with explicit user grants. |
| Audit | Sensitive operations and denied authorizations create audit events. |
| Source of truth | PostgreSQL is the only source of truth. |
| AI boundary | The API never calls an LLM in the product. |
| Tests | Permission, review, search, context pack, session, admin, error, and audit invariants are automated. |

## Working From Specs

Before implementing a feature, read the matching Markdown spec, Gherkin feature, and ADR. Any behavior change must update the spec first, then implementation, then tests. If a requirement is missing or ambiguous, record it in `specs/implementation/open-questions.md` or create an ADR before coding the decision.
