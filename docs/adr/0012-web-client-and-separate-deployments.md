# ADR-0012: Web Client In A Monorepo With Separate Deployments

Status: Accepted
Date: 2026-07-01

## Context

Nexus is an API-first product (ADR-0001). The minimal UI in the roadmap Phase 5
needs a real client. We want the frontend and the API to live in one repository
(shared history, atomic cross-cutting changes, one source of truth for specs),
but we do **not** want to couple them at runtime: they must deploy separately and
in isolation so either can scale, roll back, or move hosting independently.

The web client also needs an authenticated login. The product login is Google
OIDC (ADR-0010), but the web OIDC browser flow is not implemented yet, and a real
Google client requires operator-provided credentials. Local development and the
first end-to-end UI must work without that.

## Decision

1. **Monorepo, not a runtime monolith.** The React web client lives in `web/` at
   the repository root, alongside the Python API in `app/`. The API never serves
   the SPA bundle. Each is built and deployed as an independent artifact.
2. **Cross-origin integration.** The API enables CORS for the configured web
   origins (`NEXUS_CORS_ORIGINS`, default `http://localhost:5173`). The web client
   targets the API through a build-time base URL (`VITE_API_URL`, default
   `http://localhost:8000`). No shared process, no reverse-proxy requirement.
3. **API-only client.** The web client uses the versioned `/v1` API exclusively.
   It never reaches PostgreSQL, search indexes, or future vector stores directly,
   and it respects the review workflow (shared memory may be `pending_review`).
4. **Local dev login.** A flag-guarded endpoint `POST /v1/auth/web/dev-login`
   (enabled only when `NEXUS_DEV_LOGIN=true`, `404` otherwise) issues a normal
   Nexus web session for a seeded user by email. It reuses
   `AuthService.create_session_for_user` and never bypasses authorization: the
   resulting session has full user permissions and no session capability
   restrictions, exactly like a real login would. Real Google OIDC web login
   remains the production path and a follow-up.
5. **Readable projects endpoint.** `GET /v1/projects` lists the projects the actor
   can see (effective project role, or any project for org admins) so the UI can
   populate project pickers and filters without requiring admin endpoints.

## Consequences

- Frontend and backend can be deployed to different hosts/CDNs and versioned
  independently; the only contract between them is the `/v1` HTTP API and CORS.
- The API gains a small, non-product, flag-guarded dev surface. It is disabled by
  default and must never be enabled in production.
- `standards/frontend/repository-structure.md` defines the `web/` layout; the root
  layout in `standards/backend/repository-structure.md` notes the sibling `web/`.
- Search/context-pack write path was corrected to emit `setweight` weights as
  untyped SQL literals so the PostgreSQL `search_vector` update works (it had never
  run against PostgreSQL in tests).

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| FastAPI serves the built SPA (runtime monolith) | Couples deploy/scaling/rollback of two very different artifacts; the user wants isolated deployments. |
| Separate repositories | Loses atomic spec+client changes and a single source of truth. |
| Implement Google OIDC web flow now | Requires operator credentials; blocks the first local end-to-end UI. Deferred, not replaced. |
| Reuse admin endpoints for project pickers | Would force the UI to require `is_org_admin`; wrong for normal users. |

## Links

| Spec | File |
| --- | --- |
| API | `specs/api/rest-api.md` |
| UI/CLI | `specs/product/ui-cli.md` |
| Auth/OIDC | `docs/adr/0010-oidc-short-lived-user-sessions.md` |
| Frontend structure | `standards/frontend/repository-structure.md` |
