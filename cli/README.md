# Nexus CLI

`nexus` is the command-line client for the Nexus governed shared memory API. It lets a
developer (or an AI tool acting on their behalf) sign in through browser SSO and capture,
search, and assemble reusable memory — always through the API, never the database.

## Install

The CLI is a standalone package with **no third-party runtime dependencies** (standard
library only). Install it with `pipx` or `uv`:

```sh
pipx install ./cli          # from a checkout
# or
uv tool install ./cli
```

## Authentication

`nexus login` starts a browser SSO flow. The CLI is a public client: it never holds the
OIDC client secret. It exchanges an approved one-time device authorization for
short-lived Nexus credentials and stores the **refresh token** in
`~/.config/nexus/credentials.json` with `0600` permissions (override with
`NEXUS_CREDENTIALS_FILE`). The access token is short-lived and refreshed automatically.

```sh
export NEXUS_API_URL=https://api.nexus.example.com   # defaults to http://localhost:8000
nexus login
nexus whoami
```

## Usage

```sh
# Capture a decision (proposed for review unless you can publish directly)
nexus memory add \
  --project CECW \
  --type decision \
  --visibility project \
  --title "Payment sync retries must use idempotency keys" \
  --body "Concurrent retries can process duplicate events without an idempotency key." \
  --tag payments --tag sync \
  --source-tool codex

# Read the body from stdin
echo "long body..." | nexus memory add --type note --title "Note" --body -

# Search authorized memory
nexus search --query "idempotency keys" --project CECW --type decision

# Assemble a task context pack (rendered as Markdown locally)
nexus context-pack --project CECW --task "Continue payment sync retries" --max-items 20

nexus logout
```

Shared memory is governed: when the API returns `pending_review`, the CLI says the entry
was proposed for review and does not claim it is active.

## Configuration

| Variable | Purpose |
| --- | --- |
| `NEXUS_API_URL` | API base URL (default `http://localhost:8000`). |
| `NEXUS_CREDENTIALS_FILE` | Override the credentials file path. |

## Development

```sh
cd cli
uv run ruff check .
uv run basedpyright
uv run pytest
```
