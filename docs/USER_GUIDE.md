# Nexus User Guide

Everything you need to **install, use, configure, and integrate** Nexus — the
governed shared-memory layer for teams that work with AI tools.

This guide is for people who *use* Nexus (developers, reviewers, and the AI tools
acting on their behalf). If you operate the service, jump to
[Self-hosting Nexus](#self-hosting-nexus) and the
[production runbook](../standards/deployment.md).

---

## Table of contents

1. [What Nexus is](#what-nexus-is)
2. [Concepts you need to know](#concepts-you-need-to-know)
3. [Choosing a surface: CLI vs. web](#choosing-a-surface-cli-vs-web)
4. [The `nexus` CLI](#the-nexus-cli)
   - [Install](#install)
   - [Point the CLI at your server](#point-the-cli-at-your-server)
   - [Sign in](#sign-in)
   - [Capture memory](#capture-memory)
   - [Search](#search)
   - [Context packs](#context-packs)
   - [Configuration reference](#configuration-reference)
   - [Command reference](#command-reference)
5. [The web app](#the-web-app)
6. [Integrating Nexus with AI tools & scripts](#integrating-nexus-with-ai-tools--scripts)
7. [Self-hosting Nexus](#self-hosting-nexus)
8. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## What Nexus is

Nexus is a **governed shared memory layer** for organizations and projects that
work with AI tools. Instead of losing decisions, failed attempts, and hard-won
procedures inside individual chat histories, your team captures them as
structured **memory entries** that can be searched and re-assembled later — by a
person or by an AI tool acting on that person's behalf.

Three things make Nexus different from a wiki or a notes app:

- **API-first.** Every client (CLI, web, AI tool) goes through the same `/v1`
  REST API. Nothing touches the database or search index directly.
- **Users are the permission actors.** AI tools never have their own identity;
  they always act *on behalf of* a signed-in user and are recorded as the
  `source_tool`.
- **Shared memory is governed.** Private memory is instant; memory you propose to
  a group, project, or the whole organization can require **human review** before
  it becomes active.

There is **no LLM inside the Nexus API** — the intelligence lives in your tools.
Nexus is the trustworthy, authorized store those tools read from and write to.

---

## Concepts you need to know

You will see these terms throughout the CLI and web app.

| Term | Meaning |
| --- | --- |
| **Organization** | The top-level tenant. You only ever see memory from your own org. |
| **Project** | A body of work, identified by a short **key** (e.g. `CECW`). Owned by a group. |
| **Group / team** | A set of users; projects are owned by groups. |
| **Memory entry** | The primary unit: one decision, problem, solution, etc. Has a title, body, type, tags, visibility, and status. |
| **Source tool** | The tool that created the entry on your behalf (e.g. `codex`, `nexus-cli`). Recorded for provenance. |
| **Evidence** | Optional supporting references attached to a memory (quotes, code refs, URLs, tickets, PRs, commits…). |
| **Grant** | An explicit share of a *restricted* memory with a specific user (`viewer`, `editor`, or `manager`). |
| **Context pack** | A structured, authorized bundle of memory assembled for a task or handover, grouped by type. |

### Memory types

Pick the `--type` that best describes what you are capturing:

`decision` · `problem` · `solution` · `failed_attempt` · `procedure` · `risk` ·
`open_question` · `task` · `note`

### Visibility scopes

Visibility (`--visibility`) controls who can read an entry. **Private is the
default** if you set nothing.

| Scope | Who can read it | Notes |
| --- | --- | --- |
| `private` | Only you | The default when visibility is omitted. |
| `restricted` | You + users you explicitly grant | Share via grants. |
| `group` | Members of a group | Requires `--group-id`. |
| `project` | People with access to the project | Requires `--project`. May need review. |
| `organization` | Everyone in your org | May need review. |

### Statuses & review

When you propose shared memory you may not be able to publish it directly. In
that case the entry is created as **`pending_review`** and a reviewer or
maintainer must approve it before it becomes **`active`**. The CLI tells you
plainly when this happens and does **not** pretend the entry is live.

Possible statuses: `pending_review` · `active` · `needs_review` · `rejected` ·
`deprecated` · `archived`.

---

## Choosing a surface: CLI vs. web

Nexus ships two clients over the same API. Use whichever fits the moment.

| Use the **CLI** when… | Use the **web app** when… |
| --- | --- |
| You (or an AI tool) are capturing memory from a terminal or a script | You want to browse, read, and search visually |
| You want to assemble a context pack into your editor/agent | You are **reviewing** proposed memory (approve/reject) |
| You want scripted, non-interactive automation | You are creating memory with a form and rich evidence |
| — | You are **approving a CLI sign-in** from your browser |

They interoperate: sign in on the CLI, review in the web app, and both read the
same governed store.

---

## The `nexus` CLI

`nexus` is a standalone command-line client with **no third-party runtime
dependencies** (Python standard library only). It signs in through browser SSO
and captures, searches, and assembles memory — always through the API.

### Install

You need Python 3.12+. Install with `pipx` or `uv`:

```sh
# From a checkout of this repository:
pipx install ./cli
# or
uv tool install ./cli
```

This puts a `nexus` command on your `PATH`. Verify it:

```sh
nexus --help
```

### Point the CLI at your server

By default the CLI talks to `http://localhost:8000`. Point it at your real
Nexus API **once** and forget it:

```sh
nexus config set api_url https://api.nexus.example.com
```

The API URL is stored in your config and, after you log in, in your credentials
file — so day-to-day commands need no environment variables. (Full precedence and
env-var overrides are in the [configuration reference](#configuration-reference).)

### Sign in

`nexus login` starts a **browser SSO device flow**. The CLI is a *public client*:
it never holds the OIDC client secret.

```sh
nexus login
```

What happens:

1. The CLI asks the API to start an authorization and prints a **verification
   URL**, then tries to open it in your browser.
2. In the browser you sign in (Google OIDC in production) and land on the
   **Approve CLI sign-in** page. It shows which client is asking and the
   capabilities it requested. Click **Approve**.
3. The CLI, which has been polling, receives short-lived credentials. It stores
   the **refresh token** in `~/.config/nexus/credentials.json` with `0600`
   permissions. The access token is short-lived and refreshed automatically on
   every command.

Confirm who you are, and sign out when done:

```sh
nexus whoami     # shows user_id, org_id, client type, capabilities
nexus logout     # revokes the session server-side and clears local credentials
```

> If a command says *"Your session expired. Run 'nexus login' again."*, just log
> in again — the refresh token rotates on every use and eventually expires.

### Capture memory

Create an entry with `nexus memory add`. `--type`, `--title`, and `--body` are
required; everything else is optional.

```sh
# A project decision, proposed for review unless you can publish directly
nexus memory add \
  --project CECW \
  --type decision \
  --visibility project \
  --title "Payment sync retries must use idempotency keys" \
  --body "Concurrent retries can process duplicate events without an idempotency key." \
  --rationale "Prevents double-charging customers." \
  --tag payments --tag sync \
  --source-tool codex
```

Read the body from **stdin** with `--body -` (handy for long or generated text):

```sh
echo "long body…" | nexus memory add --type note --title "Note" --body -
```

Notes on the flags:

- `--project CECW` — the project **key**. The CLI resolves it to an id for you;
  if no visible project has that key you get a clear error.
- `--visibility` — one of the [visibility scopes](#visibility-scopes). Omit it for
  private.
- `--group-id <uuid>` — required for `--visibility group`.
- `--tag` — repeat for multiple tags.
- `--source-tool` — who is capturing this (e.g. `codex`, `claude`). Defaults to
  your configured `source_tool`, then to `nexus-cli`.
- `--source-ref` — an optional external reference for provenance.

The command prints the new id and the status. If shared memory came back as
`pending_review`, it tells you it was **proposed for review and is not active
yet**.

### Search

Search only returns memory you are **authorized** to read:

```sh
nexus search --query "idempotency keys" --project CECW --type decision
```

- `--query` is required.
- `--type` and `--tag` can be repeated to narrow results.
- `--project` scopes to a project key (falls back to your `default_project`).
- `--limit` caps results (default 10).

Each result prints as `- [type] title (status)`.

### Context packs

Assemble a task-focused, authorized bundle of memory — grouped by type and
rendered as **Markdown locally**, ready to paste into an editor or agent prompt:

```sh
nexus context-pack \
  --project CECW \
  --task "Continue payment sync retries" \
  --query "idempotency" \
  --max-items 20
```

- `--task` is required (what you're about to do).
- `--query` optionally focuses the retrieval.
- `--max-items` caps the pack size (default 20).

The output is a `# Context pack: <task>` document with sections like *Decisions*,
*Problems*, *Solutions*, *Failed attempts*, *Risks*, *Procedures*, *Open
questions*, *Tasks*, *Notes*, plus any **Warnings** the API attached.

### Configuration reference

Persist non-secret settings so you don't repeat flags. Config lives in
`${XDG_CONFIG_HOME:-~/.config}/nexus/config.json`.

```sh
nexus config set api_url https://api.nexus.example.com  # used by login and all commands
nexus config set default_project CECW                   # default for add/search/context-pack
nexus config set source_tool codex                      # default source_tool for memory add
nexus config list                                       # show everything
nexus config get api_url                                # print one value
nexus config path                                       # print the config file location
nexus config unset default_project                      # remove a key
```

Values resolve by precedence: **CLI flag → environment variable → `config.json` →
built-in default.**

| Setting | Config key | Env override | Flag |
| --- | --- | --- | --- |
| API base URL | `api_url` | `NEXUS_API_URL` | `nexus login --api-url` |
| Default project | `default_project` | — | `--project` |
| Default source tool | `source_tool` | — | `--source-tool` |

| Environment variable | Purpose |
| --- | --- |
| `NEXUS_API_URL` | Overrides `api_url` (default `http://localhost:8000`). |
| `NEXUS_CONFIG_FILE` | Override the config file path. |
| `NEXUS_CREDENTIALS_FILE` | Override the credentials file path — useful for juggling multiple environments (e.g. staging vs. prod). |

> **Multiple environments:** point `NEXUS_CREDENTIALS_FILE` (and optionally
> `NEXUS_CONFIG_FILE`) at per-environment paths, or just `nexus config set
> api_url` and `nexus login` again to switch.

### Command reference

| Command | What it does |
| --- | --- |
| `nexus login [--api-url URL]` | Browser SSO sign-in; stores a refresh token. |
| `nexus logout` | Revoke the session and forget local credentials. |
| `nexus whoami` | Show the signed-in user, org, client type, and capabilities. |
| `nexus memory add …` | Create a memory entry (see flags above). |
| `nexus search --query … [--project --type --tag --limit]` | Search authorized memory. |
| `nexus context-pack --task … [--project --query --max-items]` | Build a Markdown context pack. |
| `nexus config <list\|get\|set\|unset\|path>` | Manage persistent user configuration. |

Exit codes: `0` success, `1` a runtime/API error (message on stderr), `2` a
usage error (e.g. unknown config key).

---

## The web app

The web UI is a React single-page app (TanStack Router). It talks to the same
`/v1` API over CORS and never touches the database directly. Your operator gives
you its URL (e.g. `https://app.nexus.example.com`).

### Signing in

- **Production:** click sign in and authenticate with **Google** (OIDC). Sessions
  are short-lived; you may be asked to sign in again periodically.
- **Local/dev:** if the operator enabled dev-login, you can sign in with a seeded
  email (this never runs in production).

### What you can do

| Page | Purpose |
| --- | --- |
| **Home / Memory list** | Browse memory you're authorized to see. |
| **Search** | Full-text search across authorized memory. |
| **Memory detail** | Read an entry with its evidence and source context. |
| **New memory** | Create an entry with a form, tags, visibility, and evidence. |
| **Review** | Reviewers/maintainers approve or reject `pending_review` entries. |
| **Context pack** | Assemble a task pack in the browser. |
| **Approve CLI sign-in** (`/cli/approve`) | Approve or deny a `nexus login` request. |

### Approving a CLI sign-in

When you run `nexus login`, the browser opens the **Approve CLI sign-in** page.
It shows the requesting client's name, the **requested capabilities**, and the
**maximum visibility scope**. If you aren't signed in, you'll be prompted to
first. Approve only if *you* started the login from your terminal; then return to
the terminal, which is now signed in. You can also **Deny** — nothing is granted.

---

## Integrating Nexus with AI tools & scripts

Nexus is designed for AI tools and automation to capture and retrieve memory *on
behalf of a real user*. The CLI is the simplest integration surface.

**Principles**

- The AI tool has **no identity of its own**. A human signs in with `nexus
  login`; the tool reuses those credentials and records itself via
  `--source-tool` (stored as `source_kind = ai_cli`).
- Everything the tool can read or write is bounded by that human's
  **authorization** — the tool can never exceed the user's permissions.
- Shared memory the tool proposes may land in **review**; treat a
  `pending_review` result as *proposed*, not *published*.

**Typical agent loop**

```sh
# 1. Pull relevant, authorized context before working on a task
nexus context-pack --project CECW --task "Fix flaky payment retry test" > context.md

# 2. …the agent does its work using context.md…

# 3. Capture what was learned, attributed to the tool
echo "Root cause: retries lacked idempotency keys; added keys keyed on event id." \
  | nexus memory add \
      --project CECW --type solution --visibility project \
      --title "Fixed flaky payment retry test" --body - \
      --tag payments --source-tool my-agent
```

**Tips for non-interactive use**

- Run `nexus login` once as the human; subsequent tool commands refresh silently.
- Set defaults so scripts stay short: `nexus config set default_project CECW`
  and `nexus config set source_tool my-agent`.
- Use `--body -` to pipe generated content in; avoid shell-quoting large bodies.
- Check the **exit code** (`0` = ok) and read stdout — the CLI prints the created
  id and whether it needs review.
- Isolate environments with `NEXUS_CREDENTIALS_FILE` when a runner serves
  multiple users or stages.

> **Direct API access.** Anything the CLI does is a thin wrapper over the `/v1`
> REST API, so tools can call the API directly instead. Auth is a bearer access
> token obtained from the browser SSO / refresh flow. See
> [`specs/api/rest-api.md`](../specs/api/rest-api.md) for the endpoint contracts.

---

## Self-hosting Nexus

Nexus ships as **two independently deployed artifacts** (ADR-0012): the FastAPI
**API** and the React **web SPA**. PostgreSQL 18.4 is the only source of truth.

### Try it locally

```sh
# 1. Database
docker compose up -d postgres
uv run alembic upgrade head

# 2. Seed a demo org, users, projects, and memory
uv run python -m scripts.seed_dev

# 3. API with local dev-login enabled
NEXUS_DEV_LOGIN=true uv run uvicorn app.main:app --reload   # http://localhost:8000

# 4. Web client (separate terminal)
cd web
bun install
bun run dev    # http://localhost:5173, calls the API at http://localhost:8000
```

Sign in on the web login page with a seeded email such as `pablo@aircury.com`
(maintainer/admin), `fabio@aircury.com` (contributor), or `carlos@aircury.com`
(viewer). Dev-login only works when `NEXUS_DEV_LOGIN=true` and never runs in
production, where **Google OIDC** is the login path.

### Production: serverless on AWS

Production runs **serverless on AWS, provisioned with the AWS CDK (TypeScript)**
(ADR-0013), as two independent stacks (`Nexus-Api-<env>`, `Nexus-Web-<env>`):

- **API** → AWS **Lambda** (the root `Dockerfile` as a container image + the AWS
  Lambda Web Adapter, so `uvicorn` runs unchanged) behind an **API Gateway HTTP
  API**.
- **Web SPA** → static build on **S3**, served by **CloudFront**.
- **Database** → a new `nexus` database inside a **pre-existing RDS PostgreSQL**
  instance (CDK references it; it is not provisioned here).

```sh
cd infra
npm install
npx cdk diff && npx cdk deploy --all     # provision/update both stacks
aws ecs run-task ...                      # one-shot Fargate migrate (see infra/README.md)
```

Key operational rules:

- The API image **does not** run migrations at startup — a one-shot **Fargate
  migrate task** (same image, `alembic upgrade head`) runs as a **discrete step**,
  before traffic shifts.
- Secrets (`DATABASE_URL`, `NEXUS_TOKEN_SECRET`, `NEXUS_OIDC_CLIENT_SECRET`) live in
  **SSM Parameter Store (`SecureString`)** and are **resolved at runtime** — never
  plaintext in the Lambda definition or env vars. The OIDC client secret is
  **server-only** — never ship it to the CLI or the SPA.
- `NEXUS_DEV_LOGIN` **must be unset** in production.
- The SPA inlines `VITE_API_URL` at build time — set it before building and
  rebuild/re-upload if it changes.
- Health endpoints (`GET /health`, `/health/live`, `/health/ready`) serve deploy
  smoke tests and canaries (503 when the DB is unreachable).

`docker-compose.prod.yml` remains only a **local, prod-like integration harness**,
not the deploy path.

The full runbook — SSM secrets, consuming the existing RDS, Google OIDC
provisioning, CDK stacks, scaling/connections, backup/restore, and TLS — is in
**[`standards/deployment.md`](../standards/deployment.md)**.

### Environment variables (API)

**Secrets** — any env var whose value starts with **`ssm:`** is treated as a
pointer to an **SSM Parameter Store (`SecureString`)** parameter and resolved
(decrypted) at runtime. In production set e.g.
`NEXUS_TOKEN_SECRET=ssm:/nexus/prod/token-secret`; locally set the plain value (or
use `.env`). The same variable name is used in both cases.

| Secret | Env var | Local value | Production value | Purpose |
| --- | --- | --- | --- | --- |
| Database URL | `DATABASE_URL` | plain URL | `ssm:/nexus/prod/database-url` | SQLAlchemy/psycopg URL (contains the DB password). |
| Token secret | `NEXUS_TOKEN_SECRET` | plain value | `ssm:/nexus/prod/token-secret` | 24+ char secret signing tokens, hashes, and OIDC state. |
| OIDC client secret | `NEXUS_OIDC_CLIENT_SECRET` | plain value | `ssm:/nexus/prod/oidc-client-secret` | Google OAuth client secret — **server-only**. |

**Non-secret config** — plain env vars on the API Lambda:

| Variable | Required | Purpose |
| --- | --- | --- |
| `NEXUS_OIDC_CLIENT_ID` | Yes (prod) | Google OAuth client id (public). |
| `NEXUS_OIDC_ORG_SLUG` | Optional | Org that OIDC logins map to (default `aircury`). |
| `NEXUS_PUBLIC_BASE_URL` | Yes | Public API URL; OIDC redirects and CLI links are built from it. |
| `NEXUS_WEB_BASE_URL` | Yes | Public SPA URL. |
| `NEXUS_WEB_LOGIN_REDIRECT_URIS` | Yes | Allowlist of SPA callback URLs for OIDC. |
| `NEXUS_CORS_ORIGINS` | Yes | Cross-origin allowlist for the web client. |
| `NEXUS_DEV_LOGIN` | Must be unset in prod | Local-only password-less login. |
| `VITE_API_URL` (web, build-time) | Yes | Public API URL inlined into the SPA bundle. |

---

## Troubleshooting & FAQ

**`nexus` command not found.** Ensure `pipx`/`uv` tool bins are on your `PATH`
(`pipx ensurepath`), then open a new shell.

**Login never completes / "expired before it was approved".** You must approve the
request in the browser before it times out. Re-run `nexus login` and click
**Approve** on the CLI approval page. Check that `api_url` points at the right
server.

**"Not signed in. Run 'nexus login' first."** You have no local credentials for
this environment — log in (or set `NEXUS_CREDENTIALS_FILE` to the right file).

**"Your session expired. Run 'nexus login' again."** The refresh token is no
longer valid; sign in again.

**"No visible project with key 'X'."** The project key doesn't exist or you lack
access to it. Check the key and your project membership.

**My shared memory isn't showing up as active.** It was created as
`pending_review` and needs a reviewer/maintainer to approve it in the **Review**
page of the web app.

**Search returns nothing I expected.** Search is authorization-scoped — you only
see memory you're allowed to read. Widen the query, check the `--project`/`--type`
filters, or confirm your access.

**Where are my credentials stored?** The refresh token lives in
`~/.config/nexus/credentials.json` (`0600`); non-secret config in
`~/.config/nexus/config.json`. Override both with `NEXUS_CREDENTIALS_FILE` /
`NEXUS_CONFIG_FILE`.

**Can AI tools bypass my permissions?** No. Tools act on behalf of a user and are
bounded by that user's authorization; they are recorded as the `source_tool`.

---

### See also

- [`cli/README.md`](../cli/README.md) — CLI quick reference.
- [`README.md`](../README.md) — project overview, principles, and stack.
- [`standards/deployment.md`](../standards/deployment.md) — production runbook.
- [`specs/api/rest-api.md`](../specs/api/rest-api.md) — REST API contracts.
- [`specs/product/overview.md`](../specs/product/overview.md) — product goals and workflows.
