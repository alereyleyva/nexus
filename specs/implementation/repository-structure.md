# Repository Structure Spec

## Purpose

The product should use a modular FastAPI structure that keeps identity, authorization, memory, search, context packs, and audit concerns separated while remaining a single deployable application.

## Recommended Layout

```text
nexus/
README.md
pyproject.toml
.env.example

app/
  main.py
  config.py
  dependencies.py

  common/
    ids.py
    errors.py
    pagination.py
    time.py
    logging.py

  db/
    base.py
    session.py
    migrations/

  modules/
    identity/
      models.py
      schemas.py
      repository.py
      service.py
      router.py

    auth/
      models.py
      schemas.py
      repository.py
      service.py
      router.py

    admin/
      schemas.py
      service.py
      router.py

    groups/
      models.py
      schemas.py
      repository.py
      service.py
      router.py

    projects/
      models.py
      schemas.py
      repository.py
      service.py
      router.py

    authorization/
      service.py
      policies.py
      roles.py
      readable_queries.py

    memory_entries/
      models.py
      schemas.py
      repository.py
      service.py
      router.py

    search/
      schemas.py
      service.py
      router.py
      indexer.py

    context_packs/
      schemas.py
      service.py
      router.py

    audit/
      models.py
      schemas.py
      repository.py
      service.py

tests/
  conftest.py
  test_auth_sessions.py
  test_admin_api.py
  test_project_effective_roles.py
  test_memory_permissions.py
  test_memory_creation_review.py
  test_search_permissions.py
  test_context_pack_permissions.py
  test_audit.py
```

## Boundary Rules

| Rule | Requirement |
| --- | --- |
| Routers | Validate API input and delegate to services. |
| Services | Enforce business rules and call repositories. |
| Repositories | Encapsulate database access. |
| Authorization | Centralize permission checks and readable memory query. |
| Audit | Audit service is called by mutating/sensitive workflows. |
| Search | Search must use authorization readable query. |
| Context packs | Context pack service must use search/readable query, not direct unrestricted DB reads. |

## Module Responsibilities

| Module | Responsibilities |
| --- | --- |
| `identity` | Organizations, users, org memberships, active user state. |
| `auth` | OIDC provider adapters, CLI login, auth sessions, access JWT validation, refresh rotation, session revocation. |
| `admin` | User, org membership, group, project, and membership management API. |
| `groups` | Groups, group memberships, lead/member roles. |
| `projects` | Projects, owning group, project memberships, timeline. |
| `authorization` | Role resolution, policy checks, readable memory query. |
| `memory_entries` | CRUD, evidence, grants, review, visibility, archive/soft delete. |
| `search` | FTS vector maintenance, filters, ranking, search audit. |
| `context_packs` | Authorized memory selection and grouping. |
| `audit` | Audit event persistence and metadata safety. |

## Non-Goals For Structure

| Non-goal | Decision |
| --- | --- |
| Microservices | Do not split services in this architecture. |
| Generic IAM module | Use explicit authorization policies. |
| Vector worker | Future semantic search only. |
| LLM provider module | Not part of the API. |
