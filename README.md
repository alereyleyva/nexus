# Nexus

**Governed shared memory for teams that build with AI.**

Nexus is the memory layer your AI tools have been missing. Decisions, problems,
solutions, failed attempts, procedures, risks, open questions, tasks, and notes —
captured once, reused everywhere, and always subject to who is actually allowed to
see them.

AI assistants forget everything between sessions. Nexus gives them a durable,
shared, and *governed* place to remember — so the knowledge your team generates
stops evaporating into disconnected chat histories.

## Why Nexus

- **Reusable knowledge, not scattered chats.** Structured memory entries that
  outlive any single conversation, tool, or teammate.
- **Governed by design.** Every read and write is checked against real identity
  and authorization. Private by default; sharing is deliberate and reviewable.
- **API-first and tool-agnostic.** Any AI assistant, IDE plugin, or script can
  contribute and retrieve memory through one clean REST API.
- **A single source of truth.** PostgreSQL holds the canonical memory; search and
  context packs return only what the caller is authorized to see.
- **No LLM lock-in.** The intelligence lives in your tools. Nexus stays a fast,
  predictable, auditable system of record.

## What you can store

Nexus treats a **memory entry** as the primary unit — no sessions, batches, or
repositories required. Entries can capture:

Decisions · Problems · Solutions · Failed attempts · Procedures · Risks ·
Open questions · Tasks · Notes

Each entry carries visibility (private, group, project, or organization), optional
evidence, and a full audit trail.

## How it works

1. An AI tool submits a structured memory entry **on behalf of a real user**.
2. Nexus validates identity and authorization, then persists the entry in
   PostgreSQL — the source of truth.
3. Shared memory (group, project, or organization) can require review before it
   becomes visible.
4. Search and **context packs** return only authorized memory, ready to drop into
   a task, handover, or new AI session.

## Product principles

| Principle | What it means |
| --- | --- |
| Memory entry is the primary unit | No AI sessions, messages, or batches required to store knowledge. |
| Users are permission actors | AI tools act on behalf of users and are recorded as source tools. |
| API is the only entry point | No client touches PostgreSQL, vector stores, or search indexes directly. |
| PostgreSQL is the source of truth | Any future vector store is a derived index, never authoritative. |
| Context and visibility are separate | A memory can reference a project without being visible to it. |
| Private by default | Missing visibility means `private`. |
| Shared memory is governed | Group, project, and organization memory may require review. |
| No LLM in the API | AI happens in your clients and tools, never inside Nexus. |

## Quickstart

Run the full stack locally in four steps from the repository root:

```sh
# 1. Database
docker compose up -d postgres
uv run alembic upgrade head

# 2. Seed a demo org, users, projects, and memory
uv run python -m scripts.seed_dev

# 3. API (with local dev-login enabled)
NEXUS_DEV_LOGIN=true uv run uvicorn app.main:app --reload

# 4. Web client (separate terminal)
cd web
bun install
bun run dev   # http://localhost:5173, talks to the API at http://localhost:8000
```

Sign in on the web login page with a seeded email such as `pablo@aircury.com`
(maintainer/admin), `fabio@aircury.com` (contributor), or `carlos@aircury.com`
(viewer). Dev-login only works when `NEXUS_DEV_LOGIN=true` and never runs in
production, where Google OIDC is the login path.

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** — install, use, configure, and integrate
  Nexus. Start here if you *use* Nexus or wire an AI tool into it.
- **[CLI reference](cli/README.md)** — the `nexus` command quick reference.
- **[Web client](web/README.md)** — the browser app and its pages.
- **[REST API contract](specs/api/rest-api.md)** — endpoints for direct integration.

## Under the hood

Nexus is built with FastAPI, Pydantic v2, SQLAlchemy 2, and PostgreSQL, and runs
serverless on AWS. The React + TanStack Router web SPA deploys separately and
talks to the API over `/v1`.

For contributors and operators:

- **[Specifications](specs/README.md)** — the canonical, spec-driven product and
  domain definitions.
- **[Engineering standards](standards/README.md)** — repository layout, code
  quality, testing, and CI gates.
- **[Production runbook](standards/deployment.md)** — deploy and operate the API
  and web SPA on AWS.
- **[Infrastructure](infra/README.md)** — the AWS CDK stacks.
- **[AGENTS.md](AGENTS.md)** — operational instructions for coding agents.

> This project is developed spec-first: behavior and standards changes update the
> relevant spec or standard before the implementation and tests. See
> [`standards/spec-driven-development.md`](standards/spec-driven-development.md).
