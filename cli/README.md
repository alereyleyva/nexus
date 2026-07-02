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
  --project PAY \
  --type decision \
  --visibility project \
  --title "Payment sync retries must use idempotency keys" \
  --body "Concurrent retries can process duplicate events without an idempotency key." \
  --tag payments --tag sync \
  --source-tool codex

# Read the body from stdin
echo "long body..." | nexus memory add --type note --title "Note" --body -

# Search authorized memory
nexus search --query "idempotency keys" --project PAY --type decision

# Assemble a task context pack (rendered as Markdown locally)
nexus context-pack --project PAY --task "Continue payment sync retries" --max-items 20

nexus logout
```

Shared memory is governed: when the API returns `pending_review`, the CLI says the entry
was proposed for review and does not claim it is active.

## Configuration

Persist user configuration with `nexus config` (stored in
`${XDG_CONFIG_HOME:-~/.config}/nexus/config.json`, non-secret values only):

```sh
nexus config set api_url https://api.nexus.example.com   # used by `nexus login` and all commands
nexus config set default_project PAY                    # default project for add/search/context-pack
nexus config set source_tool codex                       # default source_tool for `memory add`
nexus config list
nexus config get api_url
nexus config unset default_project
```

Point the CLI at production once and forget it: `nexus config set api_url <prod-url>`,
then `nexus login`. The chosen URL is also stored in the credentials file, so day-to-day
commands need no environment variables.

Values resolve by precedence: **CLI flag > environment variable > `config.json` > default**.

| Setting | Config key | Env override | Flag |
| --- | --- | --- | --- |
| API base URL | `api_url` | `NEXUS_API_URL` | `nexus login --api-url` |
| Default project | `default_project` | — | `--project` |
| Default source tool | `source_tool` | — | `--source-tool` |

| Variable | Purpose |
| --- | --- |
| `NEXUS_API_URL` | Overrides `api_url` for `nexus login` (default `http://localhost:8000`). |
| `NEXUS_CONFIG_FILE` | Override the config file path. |
| `NEXUS_CREDENTIALS_FILE` | Override the credentials file path (useful for multiple environments). |

## Development

```sh
cd cli
uv run ruff check .
uv run basedpyright
uv run pytest
```
