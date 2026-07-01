# Nexus

Nexus is a governed shared memory layer for organizations and projects that work with AI tools. Developers and teams can store reusable knowledge such as decisions, problems, solutions, failed attempts, procedures, risks, open questions, tasks, and notes.

The product is intentionally API-first and simple: AI tools submit structured memory entries on behalf of real users, the API validates identity and authorization, PostgreSQL persists the source of truth, and search/context packs return only authorized memory.

## Current Status

This repository contains the canonical product specifications and an initial FastAPI backend implementation aligned to the v1 specs. The backend includes SQLAlchemy models, Alembic migration scaffolding, authorization-critical services, REST routers, audit persistence, authorized search/context packs, and behavior-first tests.

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
| `specs/features/*.feature` | Behavior specs in Gherkin. |
| `specs/traceability/project-brief-coverage.md` | Coverage map proving the original brief was decomposed into specs. |
| `standards/README.md` | Canonical index for engineering standards. |
| `standards/backend/repository-structure.md` | Required FastAPI/Python repository layout. |
| `standards/backend/internal-services.md` | Internal service responsibilities and function boundaries. |
| `standards/python/code-quality.md` | Ruff, basedpyright, pytest, coverage, and suppression policy. |
| `standards/python/style.md` | Python implementation style and layer conventions. |
| `standards/ci-quality-gates.md` | Required CI checks and coverage gates. |
| `standards/testing.md` | Mandatory test coverage and invariants. |
| `standards/spec-driven-development.md` | Rules for maintaining the project from specs. |
| `docs/decisions/resolved-questions.md` | Resolved decisions from formerly open questions. |
| `docs/adr/*.md` | Architectural Decision Records. |
| `AGENTS.md` | Operational instructions for coding agents. |

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

## Implementation Stack

| Layer | Technology |
| --- | --- |
| Runtime | Python 3.12 |
| Package manager | uv |
| API | FastAPI |
| Schemas | Pydantic v2 |
| ORM | SQLAlchemy 2 |
| Migrations | Alembic |
| Database | PostgreSQL 18.4 |
| Tests | pytest |
| Formatting/linting | Ruff |
| Typing | basedpyright |
| Coverage | coverage.py |
| Local infra | Docker Compose using `postgres:18.4-alpine` |

## Local Development Infrastructure

Start the development database from the repository root:

```sh
docker compose up -d postgres
```

The local database uses the non-secret development defaults from `.env.example`:

```text
DATABASE_URL=postgresql+psycopg://nexus:nexus_dev_password@localhost:5433/nexus
```

## Web Client

The web UI is a React + TanStack Router SPA in `web/`, styled with Tailwind from
`DESIGN.md`. It lives in this monorepo but **deploys separately** from the API and
talks to it over the `/v1` API with CORS (ADR-0012). It never accesses the database
or search indexes directly.

Run the full stack locally:

```sh
# 1. Database
docker compose up -d postgres
uv run alembic upgrade head

# 2. Seed demo org/users/projects/memory
uv run python -m scripts.seed_dev

# 3. API with local dev-login enabled
NEXUS_DEV_LOGIN=true uv run uvicorn app.main:app --reload

# 4. Web client (separate terminal)
cd web
bun install
bun run dev   # http://localhost:5173, calls the API at http://localhost:8000
```

Sign in on the web login page with a seeded email such as `pablo@aircury.com`
(maintainer/admin), `fabio@aircury.com` (contributor), or `carlos@aircury.com`
(viewer). Dev-login is disabled unless `NEXUS_DEV_LOGIN=true` and never runs in
production, where Google OIDC web login is the path.

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
| Quality gates | Ruff format/check, basedpyright, pytest, and coverage pass. |

## Working From Specs

Before implementing a feature, read the matching product spec, engineering standard, Gherkin feature, ADR, and `AGENTS.md`. Any behavior or engineering-standard change must update the spec/standard first, then implementation, then tests. If a requirement is missing or ambiguous, ask or record the decision in `docs/decisions/resolved-questions.md` before coding it.
