# Repository Structure Spec

## Purpose

Nexus is a modular FastAPI monolith. The repository structure is part of the technical contract: developers and agents should be able to locate behavior by domain, understand dependency direction, and rebuild implementation from specs.

Do not create new top-level application folders or generic utility modules unless this spec is updated first.

## Required Root Layout

```text
nexus/
  AGENTS.md
  README.md
  pyproject.toml
  uv.lock
  pyrightconfig.json
  .env.example
  docker-compose.yml
  alembic.ini

  app/
    __init__.py
    main.py
    config.py
    dependencies.py

    common/
      __init__.py
      ids.py
      errors.py
      pagination.py
      time.py
      logging.py
      security.py

    db/
      __init__.py
      base.py
      session.py
      migrations/
        env.py
        script.py.mako
        versions/

    modules/
      __init__.py
      identity/
      auth/
      admin/
      groups/
      projects/
      authorization/
      memory_entries/
      search/
      context_packs/
      audit/

  tests/
    conftest.py
    factories/
    helpers/
    integration/
    unit/
    test_auth_sessions.py
    test_admin_api.py
    test_project_effective_roles.py
    test_memory_permissions.py
    test_memory_creation_review.py
    test_search_permissions.py
    test_context_pack_permissions.py
    test_audit.py

  specs/
  docs/adr/
  typings/
  scripts/

  web/                      # React/TanStack Router web client (separate deploy)
```

The `web/` directory is the frontend client. It is part of the monorepo but builds
and deploys independently of the API and must not be imported by the Python app.
Its structure is defined in `../frontend/repository-structure.md`.

Root item responsibilities:

| Path | Responsibility |
| --- | --- |
| `AGENTS.md` | Operational instructions for coding agents. |
| `pyproject.toml` | Project metadata and Python tool configuration. |
| `uv.lock` | Locked dependency graph. |
| `pyrightconfig.json` | basedpyright/Zed/CI type-checking configuration. |
| `.env.example` | Non-secret environment variable documentation. |
| `docker-compose.yml` | Local infrastructure, including PostgreSQL with `postgres:18.4-alpine`. |
| `alembic.ini` | Alembic configuration. |
| `app/` | Runtime application package. |
| `tests/` | Automated tests. |
| `specs/` | Product, behavior, data, API, and security specs. |
| `standards/` | Engineering, implementation, quality, and agent workflow standards. |
| `docs/adr/` | Binding architectural decisions. |
| `typings/` | Local stubs for untyped third-party packages when needed. |
| `scripts/` | Small developer/maintenance scripts; no product runtime logic. |

## Application Package Rules

| File/path | Responsibility |
| --- | --- |
| `app/main.py` | Create FastAPI app, include routers, register exception handlers/middleware. No business logic. |
| `app/config.py` | Pydantic settings and environment parsing. No direct secret literals. |
| `app/dependencies.py` | Shared FastAPI dependencies such as DB session and actor context. |
| `app/common/` | Cross-cutting primitives with no dependency on product modules. |
| `app/db/` | SQLAlchemy base/session and Alembic migration environment. |
| `app/modules/` | Domain modules. All product behavior belongs here. |

`app/common` must stay small. Do not turn it into a dumping ground. If code uses product language, it belongs in a product module, not `common`.

## Standard Module Layout

Each product module should follow this shape as needed:

```text
app/modules/<module_name>/
  __init__.py
  models.py
  schemas.py
  repository.py
  service.py
  router.py
```

Optional files are allowed only when they make the module clearer:

| Optional file | Use |
| --- | --- |
| `policies.py` | Module-local policy helpers that are not global authorization rules. |
| `queries.py` | Complex reusable query builders. |
| `types.py` | Module-local protocols, aliases, or typed dicts. |
| `adapters.py` | External provider adapters owned by the module. |
| `exceptions.py` | Module-specific domain exceptions if `common.errors` is insufficient. |

Do not add `utils.py`, `helpers.py`, or `misc.py` inside runtime modules. Use a precise name that explains ownership and purpose.

## Module Responsibilities

| Module | Responsibilities |
| --- | --- |
| `identity` | Organizations, users, org memberships, active user state. |
| `auth` | OIDC provider adapters, CLI login, auth sessions, access JWT validation, refresh rotation, session revocation. |
| `admin` | User, org membership, group, project, and membership management API. |
| `groups` | Groups, group memberships, lead/member roles. |
| `projects` | Projects, owning group, project memberships, timeline. |
| `authorization` | Role resolution, policy checks, readable/reviewable memory query. |
| `memory_entries` | CRUD, evidence, grants, review, visibility, lifecycle, archive, soft delete. |
| `search` | PostgreSQL FTS vector maintenance, filters, ranking, search audit. |
| `context_packs` | Authorized memory selection and grouping. |
| `audit` | Audit event persistence and metadata safety. |

## Layer Responsibilities

| Layer file | Responsibility | Must not do |
| --- | --- | --- |
| `router.py` | HTTP input/output, dependency wiring, response schemas. | Business decisions, raw SQL, direct commits. |
| `schemas.py` | Pydantic request/response/internal DTOs. | Database access or service calls. |
| `models.py` | SQLAlchemy ORM mappings and table-level metadata. | Business workflows or API schemas. |
| `repository.py` | Persistence operations and query helpers. | Authorization decisions or commits. |
| `service.py` | Business workflow, transactions, authz, audit orchestration. | HTTP-specific response handling. |
| `policies.py` | Pure decision helpers. | Database writes or HTTP concerns. |

Services own transaction boundaries. Repositories receive a session and never commit independently.

## Dependency Direction

Allowed direction:

```text
router -> service -> repository -> models
       -> schemas
       -> common
service -> authorization/audit/other services through explicit dependencies
```

Forbidden direction:

```text
repository -> service
repository -> router
models -> service/router
common -> modules
module -> unrelated module repository directly
```

Cross-module access rules:

| Rule | Requirement |
| --- | --- |
| Service-to-service | Allowed through explicit constructor/function dependencies. |
| Repository-to-repository | Avoid. Use service orchestration or a deliberate query module. |
| Shared SQL query | Put authorization-critical memory queries in `authorization/readable_queries.py`. |
| Shared constants/enums | Prefer domain-owned definitions; do not duplicate strings. |

## Authorization-Critical Paths

Memory reads must never be implemented as ad hoc queries. The following paths must use the centralized readable/reviewable query logic:

| Path | Required base |
| --- | --- |
| Memory detail/list | `readable_memory_query`. |
| Search | `readable_memory_query` plus FTS filter. |
| Context packs | Search/readable query behavior. |
| Timeline | Only events for readable memory. |
| Review queue | `reviewable_memory_query`. |
| Future exports/vector search | Revalidate IDs through readable query. |

## Test Layout

Top-level behavior tests named in `standards/testing.md` are required. Additional tests should be organized as:

```text
tests/
  unit/
    modules/<module_name>/test_<behavior>.py
  integration/
    test_<api_or_workflow>.py
  factories/
    <domain>_factory.py
  helpers/
    auth.py
    database.py
```

Test rules:

| Rule | Requirement |
| --- | --- |
| Behavior names | Test names describe behavior, not implementation. |
| Factories | Domain factories live under `tests/factories`. |
| Helpers | Test-only helpers live under `tests/helpers`, never `app/common`. |
| Integration DB | PostgreSQL-backed tests are required for DB-specific behavior. |
| Gherkin mapping | Each feature scenario should map to at least one test or clearly named group of tests. |

## Script Rules

`scripts/` is for developer automation only:

| Allowed | Forbidden |
| --- | --- |
| One-off maintenance commands. | Runtime product logic. |
| Local setup helpers. | Hidden data migrations. |
| CI helper wrappers. | Business workflows bypassing API/services. |

Scripts must be typed, linted, and safe to run from repository root. If a script becomes part of product behavior, move it into `app/modules` and specify it.

## File Creation Rules

Before creating a new runtime file, answer:

| Question | Required answer |
| --- | --- |
| Which module owns this? | A concrete module name. |
| Which layer is it? | Router, schema, model, repository, service, policy, adapter, query, or type. |
| Which spec requires it? | Product/domain/API/security/implementation spec reference. |
| Can an existing precise file own it? | Prefer existing files unless it would become too broad. |

Do not create new architecture categories by convenience.

## Non-Goals For Structure

| Non-goal | Decision |
| --- | --- |
| Microservices | Do not split services in this architecture. |
| Generic IAM module | Use explicit authorization policies. |
| Generic `utils` package | Use precise module-owned names. |
| Vector worker | Future semantic search only. |
| LLM provider module | Not part of the API. |
