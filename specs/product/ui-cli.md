# UI And CLI Spec

## Scope

The product is API-first, but a minimal UI and CLI/plugin contract help validate the product. UI and CLI must not bypass API authorization.

## Minimal UI Views

### Project Memory

Purpose: browse authorized memory associated to a project.

Filters:

| Filter | Requirement |
| --- | --- |
| Type | Filter by memory type. |
| Status | Filter by status available to actor. |
| Tag | Filter by tags. |
| Date | Filter by created/updated date. |
| Source tool | Filter by source tool. |
| Owner | Filter by owner. |
| Visibility | Filter by visibility scope. |

### Review Queue

Purpose: review pending shared memory.

Must show:

| Field/action | Requirement |
| --- | --- |
| Title | Show memory title. |
| Type | Show memory type. |
| Body | Show memory body. |
| Rationale | Show rationale when present. |
| Evidence | Show attached evidence. |
| Confidence | Show confidence when present, not as approval. |
| Owner | Show owner. |
| Source tool | Show tool that submitted memory. |
| Proposed scope | Show target visibility. |
| Approve | Authorized reviewer can approve. |
| Reject | Authorized reviewer can reject. |
| Edit | Authorized reviewer can edit during review. |
| Mark needs review | Authorized reviewer can mark active memory as needs review. |

### Memory Detail

Purpose: inspect one authorized memory entry.

Must show:

| Field | Requirement |
| --- | --- |
| Content | Title, body, rationale. |
| State | Status and warnings. |
| Visibility | Visibility scope and group/project when relevant. |
| Project | Associated project when present. |
| Owner | Owner user. |
| Evidence | Evidence list. |
| Source context | JSON/source details. |
| Audit timeline | Basic timeline for the memory. |

### Search

Purpose: search authorized memory.

Requirement: UI search results must come from `POST /v1/search` or an equivalent authorized API path, never from direct database/index access.

### Context Pack View

Purpose: generate task context.

Form fields:

| Field | Example |
| --- | --- |
| Project | `CECW` |
| Task | `Continue payment sync retries` |
| Max items | `20` |

Result groups:

| Group | Memory type |
| --- | --- |
| Decisions | `decision` |
| Problems | `problem` |
| Solutions | `solution` |
| Failed attempts | `failed_attempt` |
| Risks | `risk` |
| Procedures | `procedure` |
| Open questions | `open_question` |

## CLI/Plugin Responsibilities

| Responsibility | Requirement |
| --- | --- |
| Authenticate | Use personal API token. |
| Capture memory | Collect memory proposed by AI or user. |
| Send structured entries | Use memory entry API contract. |
| Include source tool | Always set `source_tool`. |
| Include source ref | Set `source_ref` when available. |
| Include client entry ID | Use `client_entry_id` for idempotency when possible. |
| Include source context | Store flexible source metadata. |
| Respect review | Do not assume shared memory is active. |
| Render locally | CLI may render JSON/context packs as Markdown locally. |

Example future command:

```sh
nexus memory add \
  --project CECW \
  --type decision \
  --visibility project \
  --title "Payment sync retries must use idempotency keys" \
  --body "Concurrent retries can process duplicate events without an idempotency key." \
  --tag payments \
  --tag sync \
  --source-tool codex \
  --source-ref codex-thread-abc123
```

Example context pack command:

```sh
nexus context-pack \
  --project CECW \
  --task "Continue payment sync retry implementation" \
  --max-items 20
```

## Client Boundary Rules

| Rule | Requirement |
| --- | --- |
| API-only | UI/CLI/plugin must use the API. |
| No direct DB | Clients must not access PostgreSQL directly. |
| No direct vector store | Future vector stores stay behind the API. |
| User token | CLI/plugin acts as user through personal token. |
| No hidden activation | Shared memory responses may require review. |
