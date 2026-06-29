# AI Implementation Prompt

Use this prompt when asking an AI coding agent to build the product from specs.

```text
Build the backend for Nexus.

Product:
Nexus is a governed shared memory layer for organizations and projects. Developers use AI tools such as Codex, OpenCode, Cursor, or ChatGPT. Those tools submit structured memory entries to the API on behalf of a real user. The API does not call any LLM in this version.

Before coding, read:
- specs/README.md
- specs/product/overview.md
- specs/domain/model.md
- specs/security/authorization.md
- specs/data/schema.dbml
- specs/implementation/repository-structure.md
- specs/implementation/python-style.md
- specs/implementation/code-quality.md
- specs/implementation/ci-quality-gates.md
- specs/implementation/dependency-management.md
- specs/implementation/database-migrations.md
- specs/implementation/internal-services.md
- specs/api/rest-api.md
- specs/search/search-and-context-packs.md
- specs/security/security-observability-audit.md
- specs/implementation/testing.md
- specs/product/ui-cli.md
- specs/features/*.feature
- docs/adr/*.md

Core architectural decisions:
- Do not model AI/source conversation sessions as mandatory memory resources. Auth sessions are required for login.
- Do not create an Agent entity in the product.
- Do not create a Repository entity.
- Do not create capture batches.
- Do not implement entry versioning.
- A memory entry belongs to an organization and may optionally belong to a project.
- A project belongs to one owning group/team.
- A group/team can own many projects.
- Repository, branch, commit, PR, files, meeting data, document data, ticket data, and similar source metadata belong in source_context JSONB.
- PostgreSQL is the source of truth.
- The API is the only access path.
- Search, context packs, timeline, and detail reads must enforce the same authorization rules.

Tech stack:
- Python 3.12
- uv
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- PostgreSQL 16
- pytest
- coverage.py
- Ruff
- basedpyright
- docker-compose

Core modules:
- identity
- auth
- admin
- authorization
- groups
- projects
- memory_entries
- search
- context_packs
- audit

Tables:
- organizations
- users
- org_memberships
- groups
- group_memberships
- projects
- project_memberships
- auth_sessions
- auth_refresh_tokens
- memory_entries
- memory_entry_grants
- memory_entry_evidence
- audit_events

Memory types:
- decision
- problem
- solution
- failed_attempt
- procedure
- risk
- open_question
- task
- note

Statuses:
- pending_review
- active
- needs_review
- rejected
- deprecated
- archived

Visibility scopes:
- private
- restricted
- group
- project
- organization

Permission rules:
- Private entries are readable only by owner.
- Restricted entries are readable by owner plus explicit user grants.
- Group entries are readable by members of visibility_group_id.
- Project entries are readable by users with effective project access.
- Effective project access comes from explicit project_memberships plus membership in the owning group.
- group.member of the owning group maps to project contributor.
- group.lead of the owning group maps to project maintainer.
- Organization entries are readable by active organization members.
- Org admins do not automatically read private entries.
- Project contributors can create project-scoped entries, but they become pending_review.
- Project reviewers and maintainers can approve project-scoped entries.
- Group leads can approve group-scoped entries.
- Knowledge admins can approve organization-scoped entries.
- CLI sessions act on behalf of users and cannot exceed the user's permissions.
- Search, context packs, timeline, and detail endpoints must all use the same readable memory query.
- Pending, rejected, deprecated, and archived entries are hidden from normal search/context packs unless explicitly requested by an authorized reviewer/admin.
- Every visibility change, approval, rejection, grant change, denied authorization, search, and context pack generation must be audited.
- Every API error must use the common Problem Details envelope.

Endpoints:
- GET /health
- GET /health/live
- GET /health/ready
- GET /v1/auth/providers
- POST /v1/auth/cli/authorizations
- GET /v1/auth/cli/authorizations/{user_code}
- GET /v1/auth/oidc/{provider}/authorize
- GET /v1/auth/oidc/{provider}/callback
- POST /v1/auth/cli/token
- POST /v1/auth/session/refresh
- POST /v1/auth/session/revoke
- GET /v1/auth/me
- GET /v1/auth/sessions
- DELETE /v1/auth/sessions/{session_id}
- GET /v1/memory-entries
- POST /v1/memory-entries
- POST /v1/memory-entries:bulk
- GET /v1/memory-entries/{id}
- PATCH /v1/memory-entries/{id}
- POST /v1/memory-entries/{id}/review
- POST /v1/memory-entries/{id}/mark-needs-review
- POST /v1/memory-entries/{id}/deprecate
- POST /v1/memory-entries/{id}/archive
- DELETE /v1/memory-entries/{id}
- PATCH /v1/memory-entries/{id}/visibility
- POST /v1/memory-entries/{id}/grants
- DELETE /v1/memory-entries/{id}/grants/{grant_id}
- GET /v1/review-queue
- POST /v1/search
- POST /v1/context-packs
- GET /v1/projects/{project_id}/timeline
- GET/POST/PATCH/PUT/DELETE /v1/admin/* endpoints from specs/api/rest-api.md

Testing requirements:
- User cannot read entries from another org.
- Org admin cannot read private entries by default.
- User cannot read project entries without effective project access.
- User cannot read group entries without group membership.
- User cannot read restricted entries without explicit grant.
- CLI session cannot exceed user permissions.
- Revoked sessions cannot authenticate or refresh.
- Refresh token reuse revokes the session.
- API errors use the common Problem Details envelope.
- Search never returns unauthorized entries.
- Context packs never return unauthorized entries.
- Contributor can submit project memory but not approve it.
- Reviewer can approve project memory.
- Group lead can approve group memory.
- Knowledge admin can approve organization memory.
- Pending/rejected/deprecated/archived entries are hidden from normal search/context packs.
- Changing visibility to a wider scope requires proper approval or review workflow.

Quality requirements:
- Use `uv` and commit `uv.lock` with dependency changes.
- Use `ruff format` as the only formatter.
- Use `ruff check` as the only linter/import sorter.
- Use `basedpyright` as the strict type checker; Ruff passing is not enough.
- Use `pytest` and `coverage.py` for tests and coverage.
- Follow `specs/implementation/repository-structure.md` exactly; do not create generic `utils` modules.
- Follow `specs/implementation/python-style.md` for FastAPI, Pydantic, SQLAlchemy, service, repository, logging, and error style.
- Run or report status for `uv run ruff format --check .`, `uv run ruff check .`, `uv run basedpyright`, `uv run pytest`, and coverage gates.

If you encounter an unspecified behavior, update specs/implementation/open-questions.md or ask for a decision instead of inventing product behavior.
```
