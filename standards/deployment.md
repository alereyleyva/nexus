# Production Deployment Runbook

This runbook covers deploying the Nexus API and web client to production. It is
the operational contract for building images, provisioning identity, running
migrations, and scaling. Behavior contracts live in `specs/`; this document is
concerned with how the system is operated.

Nexus deploys as two independently shipped artifacts (ADR-0012):

- The **API** — FastAPI + SQLAlchemy, Python 3.12, synchronous — built from the
  root `Dockerfile`.
- The **web SPA** — React + TanStack Router, built with Vite — built from
  `web/Dockerfile` and served as static files by nginx.

PostgreSQL 18.4 is the only source of truth. There are no derived stores in v1.

## Artifacts

| Artifact | Build context | Notes |
| --- | --- | --- |
| API image | `Dockerfile` (repo root) | Multi-stage, uv, non-root, uvicorn workers. |
| Web image | `web/Dockerfile` | Multi-stage bun build, nginx runtime, SPA fallback. |
| Reference stack | `docker-compose.prod.yml` | postgres + one-shot migrate + api (+ optional web). |

The API image deliberately does **not** run migrations at startup. Migrations are
a separate deploy step (see below) so multiple API replicas never race on schema
changes.

## Required Environment Variables

All configuration is read from the environment (`app/config.py`). Values below
without a safe default must be set explicitly in production.

### API (server-side)

| Variable | Required | Secret | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | Yes (contains DB password) | SQLAlchemy/psycopg URL, e.g. `postgresql+psycopg://nexus:PASS@postgres:5432/nexus`. |
| `NEXUS_TOKEN_SECRET` | Yes | **Yes** | 24+ char signing secret for access tokens, refresh/login-code hashes, and OIDC state. |
| `NEXUS_OIDC_CLIENT_ID` | Yes | No | Google OAuth client id. |
| `NEXUS_OIDC_CLIENT_SECRET` | Yes | **Yes — server-only** | Google OAuth client secret. Never shipped to the CLI or SPA. |
| `NEXUS_OIDC_ORG_SLUG` | Optional | No | Org that OIDC logins map to (default `aircury`). |
| `NEXUS_PUBLIC_BASE_URL` | Yes | No | Public base URL of the API; OIDC redirect and CLI verification links are built from it. |
| `NEXUS_WEB_BASE_URL` | Yes | No | Public base URL of the SPA. |
| `NEXUS_WEB_LOGIN_REDIRECT_URIS` | Yes | No | Comma-separated allowlist of SPA callback URLs the OIDC flow may redirect to. |
| `NEXUS_CORS_ORIGINS` | Yes | No | Comma-separated cross-origin allowlist for the web client. |
| `NEXUS_DEV_LOGIN` | **Must be unset/false** | No | Local-only password-less login. **Never enable in production.** |

### Postgres (reference compose stack)

| Variable | Required | Secret | Purpose |
| --- | --- | --- | --- |
| `POSTGRES_DB` | Optional (`nexus`) | No | Database name. |
| `POSTGRES_USER` | Optional (`nexus`) | No | Database role. |
| `POSTGRES_PASSWORD` | Yes | **Yes** | Database password; also embedded in `DATABASE_URL`. |

### Web (build-time only)

| Variable | Required | Secret | Purpose |
| --- | --- | --- | --- |
| `VITE_API_URL` | Yes | No | Public API base URL. **Inlined into the bundle at build time** — pass as a `--build-arg`. Changing it requires rebuilding the web image. |

### Secret handling

- `NEXUS_TOKEN_SECRET`, `NEXUS_OIDC_CLIENT_SECRET`, and the DB password (in
  `DATABASE_URL` / `POSTGRES_PASSWORD`) are secrets. They MUST come from a secret
  manager (e.g. cloud secret store, Kubernetes Secret, Vault) and MUST NEVER be
  committed to the repo or baked into an image.
- The **OIDC client secret is server-only**. It is used solely by the API during
  the token exchange. It is never sent to the CLI or the SPA, and it must never
  appear in `VITE_*` build args or any client bundle.
- Rotating `NEXUS_TOKEN_SECRET` invalidates outstanding access tokens, refresh
  tokens, login codes, and OIDC state. Rotate deliberately.

## Google OIDC Provisioning

Production web login uses Google OIDC. Provision it once per environment:

1. In the Google Cloud console, open **APIs & Services → Credentials**.
2. Configure the OAuth consent screen for the organization if not already done.
3. Create an **OAuth 2.0 Client ID** of type **Web application**.
4. Set **Authorized JavaScript origins** to the SPA origin, e.g.
   `https://app.example.com` (the value of `NEXUS_WEB_BASE_URL`).
5. Set the **Authorized redirect URI** to the API callback:
   `${NEXUS_PUBLIC_BASE_URL}/v1/auth/oidc/google/callback`
   (e.g. `https://api.example.com/v1/auth/oidc/google/callback`).
6. Copy the generated credentials into the API environment:
   - client id → `NEXUS_OIDC_CLIENT_ID`
   - client secret → `NEXUS_OIDC_CLIENT_SECRET` (from the secret manager)
7. Set `NEXUS_WEB_LOGIN_REDIRECT_URIS` to the SPA callback the API is allowed to
   send the browser back to: `${NEXUS_WEB_BASE_URL}/auth/callback`
   (e.g. `https://app.example.com/auth/callback`).

If `NEXUS_OIDC_CLIENT_ID` / `NEXUS_OIDC_CLIENT_SECRET` are empty, OIDC is
disabled and the authorize endpoint returns 404 — do not deploy production
without them configured.

## Migrations As A Deploy Step

Alembic reads `DATABASE_URL` via `app/config.py`, so the migration runner needs
only that variable. Run migrations exactly once per deploy, before the new API
version serves traffic, and never from the API entrypoint.

```sh
# Using the built API image directly:
docker run --rm -e DATABASE_URL="$DATABASE_URL" nexus-api:latest \
  alembic upgrade head

# Or with the reference stack (the one-shot `migrate` service runs it and the
# `api` service waits for it to complete):
docker compose -f docker-compose.prod.yml run --rm migrate
```

Migrations are additive and reviewed per `standards/database-migrations.md`. With
multiple API replicas, run the single migration step first, then roll the API.

## Health And Readiness

The API exposes three endpoints for orchestrators (see `app/main.py`):

| Endpoint | Meaning | Use |
| --- | --- | --- |
| `GET /health` | Process is up; returns service/version/time. | Basic ping. |
| `GET /health/live` | Liveness. | Restart the container if this fails. |
| `GET /health/ready` | Readiness — verifies DB connectivity. | Gate traffic / rolling updates; returns 503 when the DB is unreachable. |

The API image's `HEALTHCHECK` hits `/health/ready`. Configure Kubernetes/other
orchestrator liveness probes against `/health/live` and readiness probes against
`/health/ready`.

## Horizontal Scaling

The API is stateless and safe to run as multiple replicas:

- Sessions are JWT access tokens plus DB-backed refresh/auth sessions; there is
  no in-process session state and no server-side sticky state to replicate.
- All persistent state lives in PostgreSQL, shared by every replica.
- The image runs uvicorn with multiple workers; scale further by running more
  replicas behind a load balancer.
- Run the migration step **once** per deploy (not per replica). Roll replicas
  after migrations complete.

## Backup And Restore

PostgreSQL is the single source of truth; back it up accordingly.

- Take regular logical backups, e.g. `pg_dump` / `pg_dumpall`, plus point-in-time
  recovery (WAL archiving) for production-grade durability.
- Restore with `pg_restore` / `psql` into a fresh database, then bring the API up
  against it. There are no derived indexes to rebuild in v1.
- The reference stack persists data in the `nexus_postgres_data` volume; back up
  the underlying database, not just the volume snapshot, for portable restores.
- Store backups encrypted and off-host; test restores periodically.

## TLS And Reverse Proxy

The API and nginx web server speak plain HTTP inside the deployment. Terminate
TLS at a reverse proxy / load balancer in front of both:

- Terminate HTTPS at the edge (e.g. ALB, nginx, Traefik, Cloud load balancer)
  and forward to the API on port 8000 and the web container on port 80.
- `NEXUS_PUBLIC_BASE_URL` and `NEXUS_WEB_BASE_URL` must be the public `https://`
  URLs — OIDC redirect URIs and CLI links are built from them and must match what
  Google and browsers see.
- Forward `X-Forwarded-*` headers and preserve the `X-Request-Id` header (the API
  echoes it for tracing).
- Keep the Postgres port unpublished (internal network only).

## Deploy Checklist

1. Build and push the API and web images (web needs `--build-arg VITE_API_URL`).
2. Ensure secrets are present in the secret manager and injected into the API env.
3. Confirm `NEXUS_DEV_LOGIN` is unset.
4. Run `alembic upgrade head` as a discrete step.
5. Roll the API replicas; verify `/health/ready` returns 200.
6. Smoke-test OIDC login through the SPA.
