# API Contract Spec

## API Boundary

All clients must access Nexus through the API. No client may query PostgreSQL, future pgvector/Qdrant indexes, or derived search stores directly.

## Authentication Headers

```http
Authorization: Bearer <token>
X-Request-Id: <uuid>
```

## Common Rules

| Rule | Requirement |
| --- | --- |
| Actor resolution | Every endpoint resolves an `ActorContext`. |
| Tenant isolation | Every endpoint is scoped to actor org. |
| Token scopes | Personal token calls require matching token scope. |
| Audit | Sensitive operations create audit events. |
| Authorization | Detail, search, context pack, and timeline reads use the same readable memory logic. |
| No API LLM | No endpoint calls an LLM in the product. |

## Endpoint Summary

| Method | Path | Purpose | Required token scope if using API token |
| --- | --- | --- | --- |
| POST | `/v1/memory-entries` | Create one memory entry. | `memory:create` |
| POST | `/v1/memory-entries:bulk` | Create multiple independent memory entries. | `memory:create` |
| GET | `/v1/memory-entries/{id}` | Read one authorized memory entry. | `memory:read` |
| PATCH | `/v1/memory-entries/{id}` | Edit an authorized memory entry. | `memory:update` |
| POST | `/v1/memory-entries/{id}/review` | Approve or reject memory. | `memory:review` |
| PATCH | `/v1/memory-entries/{id}/visibility` | Change visibility. | `memory:update` |
| POST | `/v1/memory-entries/{id}/grants` | Add restricted memory grant. | `grants:manage` |
| DELETE | `/v1/memory-entries/{id}/grants/{grant_id}` | Remove restricted memory grant. | `grants:manage` |
| POST | `/v1/search` | Search authorized memory. | `search:read` |
| POST | `/v1/context-packs` | Generate authorized context pack. | `context_pack:generate` |
| GET | `/v1/projects/{project_id}/timeline` | Read authorized project memory timeline. | `memory:read` |

## Create Memory

```http
POST /v1/memory-entries
```

Request:

```json
{
  "project_id": "prj_cecw",
  "type": "decision",
  "title": "Payment sync retries must use idempotency keys",
  "body": "Concurrent retries can process the same payment event more than once unless the retry path enforces idempotency.",
  "rationale": "This was found while debugging duplicate sync events.",
  "visibility_scope": "project",
  "source_kind": "ai_cli",
  "source_tool": "codex",
  "source_ref": "codex-thread-abc123",
  "client_entry_id": "local-memory-001",
  "confidence": 0.87,
  "tags": ["payments", "sync", "idempotency"],
  "source_context": {
    "repository_url": "git@github.com:company/cecw.git",
    "branch": "fix/payment-sync-retries",
    "commit_sha": "abc123",
    "files": [
      {
        "path": "services/payment_sync/retry_handler.py",
        "line_start": 82,
        "line_end": 116
      }
    ]
  },
  "evidence": [
    {
      "kind": "code_reference",
      "title": "Retry handler without idempotency",
      "quote": "The retry handler processes events without an idempotency guard.",
      "locator": {
        "file_path": "services/payment_sync/retry_handler.py",
        "line_start": 82,
        "line_end": 116
      }
    }
  ]
}
```

Response when actor is project contributor:

```json
{
  "id": "mem_123",
  "status": "pending_review",
  "visibility_scope": "project",
  "requires_review": true
}
```

Response when actor is project reviewer or maintainer:

```json
{
  "id": "mem_123",
  "status": "active",
  "visibility_scope": "project",
  "requires_review": false
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Default visibility | If omitted, use `private`. |
| Default owner | Owner is authenticated user unless future spec says otherwise. |
| Idempotency | If `client_entry_id` matches existing unique key, return existing entry instead of duplicating. |
| Evidence | Create evidence rows in same transaction. |
| Search vector | Update search vector after create. |
| Audit | Emit `memory_entry.created`. |

## Create Bulk Memory

```http
POST /v1/memory-entries:bulk
```

Bulk creates multiple independent memory entries. It does not create a batch entity.

Request:

```json
{
  "entries": [
    {
      "type": "problem",
      "title": "Duplicate payment events under retry",
      "body": "Concurrent retries can duplicate payment events.",
      "visibility_scope": "project",
      "project_id": "prj_cecw",
      "source_kind": "ai_cli",
      "source_tool": "codex",
      "source_ref": "codex-thread-abc123"
    },
    {
      "type": "failed_attempt",
      "title": "Polling-based sync was discarded",
      "body": "Polling created stale state and duplicate processing.",
      "visibility_scope": "project",
      "project_id": "prj_cecw",
      "source_kind": "ai_cli",
      "source_tool": "codex",
      "source_ref": "codex-thread-abc123"
    }
  ]
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Entry independence | Each entry has its own status, evidence, and audit behavior. |
| No capture batch | Do not add a batch table or batch resource. |
| Idempotency | Apply per-entry idempotency when `client_entry_id` is present. |

## Read Memory

```http
GET /v1/memory-entries/{id}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Use `readable_memory_entries(actor)`. |
| Denial | Unauthorized reads are denied and audited. |
| Evidence | May include evidence according to response schema implementation. |

## Edit Memory

```http
PATCH /v1/memory-entries/{id}
```

Request:

```json
{
  "title": "Updated title",
  "body": "Updated body",
  "tags": ["payments", "sync"],
  "metadata": {
    "edited_reason": "Clarify wording after review"
  }
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Apply edit rules from `../security/authorization.md`. |
| Shared active edits | Non-approver edits must not silently change active shared memory. |
| Search vector | Update search vector after content/tag/rationale changes. |
| Audit | Emit `memory_entry.updated`. |

## Review Memory

```http
POST /v1/memory-entries/{id}/review
```

Approve request:

```json
{
  "decision": "approve",
  "review_comment": "Valid and useful for the CECW project."
}
```

Reject request:

```json
{
  "decision": "reject",
  "review_comment": "The statement is too speculative and lacks evidence."
}
```

Behavior:

| Decision | Result |
| --- | --- |
| `approve` | Move `pending_review` or `needs_review` memory to `active`. |
| `reject` | Move `pending_review` memory to `rejected`. |
| Any decision | Set reviewer fields and audit event. |

## Change Visibility

```http
PATCH /v1/memory-entries/{id}/visibility
```

Request:

```json
{
  "visibility_scope": "project",
  "project_id": "prj_cecw",
  "reason": "This decision is useful for the whole project."
}
```

Possible response:

```json
{
  "id": "mem_123",
  "visibility_scope": "project",
  "status": "pending_review",
  "requires_review": true
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Audience increase | Requires approval over target scope or moves to `pending_review`. |
| Project visibility | Requires `project_id`. |
| Group visibility | Requires `visibility_group_id`. |
| Audit | Emit `memory_entry.visibility_changed`. |

## Add Grant

```http
POST /v1/memory-entries/{id}/grants
```

Request:

```json
{
  "grantee_user_id": "usr_fabio",
  "role": "viewer"
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Scope | Grants are for restricted memory and concrete users. |
| Duplicate | One grant per memory/user pair. |
| Audit | Emit `memory_entry.grant_added`. |

## Delete Grant

```http
DELETE /v1/memory-entries/{id}/grants/{grant_id}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Actor must manage grants for the memory. |
| Audit | Emit `memory_entry.grant_removed`. |

## Search

```http
POST /v1/search
```

Request:

```json
{
  "query": "payment sync retries idempotency",
  "project_id": "prj_cecw",
  "types": ["decision", "problem", "solution", "failed_attempt"],
  "statuses": ["active", "needs_review"],
  "tags": ["payments"],
  "limit": 10,
  "include_evidence": true
}
```

Response:

```json
{
  "results": [
    {
      "id": "mem_123",
      "type": "decision",
      "title": "Payment sync retries must use idempotency keys",
      "body": "Concurrent retries must use idempotency keys to avoid duplicate processing.",
      "status": "active",
      "visibility_scope": "project",
      "project_id": "prj_cecw",
      "tags": ["payments", "sync", "idempotency"],
      "score": 0.91,
      "evidence_count": 1
    }
  ]
}
```

## Context Pack

```http
POST /v1/context-packs
```

Request:

```json
{
  "project_id": "prj_cecw",
  "task": "Continue work on payment sync retries",
  "query": "payment sync retries idempotency duplicate events",
  "max_items": 20,
  "include_types": [
    "decision",
    "problem",
    "solution",
    "failed_attempt",
    "risk",
    "procedure",
    "open_question"
  ]
}
```

Response:

```json
{
  "project_id": "prj_cecw",
  "generated_at": "2026-06-28T12:00:00Z",
  "items": {
    "decisions": [
      {
        "id": "mem_123",
        "title": "Payment sync retries must use idempotency keys",
        "body": "Concurrent retries must use idempotency keys to avoid duplicate processing.",
        "status": "active",
        "evidence_count": 1
      }
    ],
    "problems": [],
    "solutions": [],
    "failed_attempts": [],
    "risks": [],
    "procedures": [],
    "open_questions": []
  },
  "warnings": [
    {
      "type": "needs_review",
      "message": "Some related memories are marked as needing review."
    }
  ]
}
```

## Project Timeline

```http
GET /v1/projects/{project_id}/timeline?from=2026-06-01T00:00:00Z&to=2026-06-28T23:59:59Z
```

Response:

```json
{
  "project_id": "prj_cecw",
  "events": [
    {
      "timestamp": "2026-06-10T12:00:00Z",
      "event_type": "memory_entry.created",
      "memory_entry_id": "mem_123",
      "type": "decision",
      "title": "Payment sync retries must use idempotency keys"
    },
    {
      "timestamp": "2026-06-12T09:00:00Z",
      "event_type": "memory_entry.approved",
      "memory_entry_id": "mem_123"
    }
  ]
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Timeline only includes events for memory the actor can read. |
| Project scope | Use requested project. |
| Time range | Respect `from` and `to`. |

## CLI Contract

CLI/plugin clients must:

| Requirement | Detail |
| --- | --- |
| Authenticate | Use personal API token. |
| Submit structured entries | Send memory proposed by AI or user. |
| Include source tool | Set `source_tool`. |
| Include source ref | Set `source_ref` when available. |
| Include idempotency | Set `client_entry_id` where possible. |
| Include source context | Use flexible JSON metadata. |
| Respect review | Do not assume shared memory becomes active automatically. |

Example future CLI:

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

Context pack CLI:

```sh
nexus context-pack \
  --project CECW \
  --task "Continue payment sync retry implementation" \
  --max-items 20
```

The CLI may render JSON as Markdown locally. The API only returns structured data.
