# Nexus Web Client

The Nexus web UI: a React + TanStack Router single-page app for browsing,
searching, creating, and reviewing governed shared memory, and for approving CLI
sign-ins. It talks to the Nexus `/v1` API over CORS and never touches the
database or search indexes directly (ADR-0012). Styling follows
[`../DESIGN.md`](../DESIGN.md) with Tailwind CSS.

> **Using the app?** See the end-user [User Guide](../docs/USER_GUIDE.md#the-web-app).
> **Deploying it?** See the [production runbook](../standards/deployment.md).

## Pages

| Route | Purpose |
| --- | --- |
| `/login` | Sign in with Google (OIDC) — or dev-login when enabled locally. |
| `/auth/callback` | Completes the OIDC login and stores the session. |
| `/cli/approve?code=…` | Approve or deny a `nexus login` request. |
| `/` (memory list) | Browse authorized memory. |
| `/memory/new` | Create a memory entry with tags, visibility, and evidence. |
| `/memory/$id` | Read an entry with its evidence and source context. |
| `/search` | Full-text search over authorized memory. |
| `/review` | Reviewers/maintainers approve or reject `pending_review` entries. |
| `/context-pack` | Assemble a task context pack in the browser. |

## Develop

Requires [Bun](https://bun.sh). The app expects the Nexus API to be reachable at
`VITE_API_URL` (defaults to `http://localhost:8000`).

```sh
bun install
bun run dev      # http://localhost:5173
```

To bring up the full local stack (database, migrations, seed data, API with
dev-login), follow [Run the full stack locally](../README.md#web-client) in the
root README, then sign in with a seeded email such as `avery.stone@example.com`.

## Test

```sh
bun run test     # Vitest
```

## Build for production

`VITE_API_URL` is **inlined into the bundle at build time**, so it must be set
before building and changing it requires a rebuild.

```sh
VITE_API_URL=https://api.nexus.example.com bun run build
```

The production image (`web/Dockerfile`) performs this multi-stage Bun build and
serves the static output with nginx (SPA history fallback). Pass the API URL as a
build arg:

```sh
docker build -t nexus-web --build-arg VITE_API_URL=https://api.nexus.example.com web/
```

## Tech stack

React 19 · TanStack Router (file-based routing) · TanStack Query · Tailwind CSS 4
· Vite · TypeScript · lucide-react · nginx (runtime).
