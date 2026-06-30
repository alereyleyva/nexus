# API Contract Spec

## API Boundary

All clients must access Nexus through the API. No client may query PostgreSQL, future pgvector/Qdrant indexes, or derived search stores directly.

The API is versioned under `/v1`. Breaking changes require a new API version or an explicit migration plan.

## Authentication Headers

Authenticated API calls use Nexus-issued access tokens from an active auth session:

```http
Authorization: Bearer <nexus_access_token>
X-Request-Id: <uuid>
```

`X-Request-Id` is required for clients that can provide one. If omitted, the API must generate a request id and return/log it.

`X-On-Behalf-Of` is not part of the product contract because session credentials already belong to a real user.

## Common Rules

| Rule | Requirement |
| --- | --- |
| Actor resolution | Every protected endpoint resolves an `ActorContext`. |
| Tenant isolation | Every protected endpoint is scoped to actor org. |
| Session capabilities | Restricted sessions require matching capability. Session capabilities restrict, never expand, user permissions. |
| Audit | Sensitive operations create audit events. |
| Authorization | Detail, list, search, context pack, review queue, and timeline reads use shared readable/reviewable memory logic. |
| No API LLM | No endpoint calls an LLM in the product. |
| Error shape | Every non-2xx API error uses the common problem envelope. |

## Resource Identifiers

Public API identifiers are canonical UUID strings in v1. Do not introduce prefixed public ids such as `mem_123`, `usr_123`, `prj_123`, or `ses_123`.

Example UUIDs in this spec are illustrative. Implementations must accept and return standard UUID strings for database-backed resources.

## Error Contract

All non-2xx responses use `application/problem+json` and the ADR-0011 error envelope.

Example:

```json
{
  "type": "https://docs.nexus.local/problems/validation-failed",
  "title": "Validation failed",
  "status": 422,
  "code": "VALIDATION_FAILED",
  "detail": "The request contains invalid fields.",
  "request_id": "req_01J...",
  "errors": [
    {
      "field": "visibility_scope",
      "code": "required",
      "message": "visibility_scope is required"
    }
  ]
}
```

Required fields:

| Field | Requirement |
| --- | --- |
| `type` | Stable URI for the problem class. |
| `title` | Short human-readable summary. |
| `status` | HTTP status code. |
| `code` | Stable Nexus error code. |
| `detail` | Safe human-readable detail. Must not include secrets, raw tokens, or full request bodies. |
| `request_id` | Request correlation id. |

Optional fields:

| Field | Requirement |
| --- | --- |
| `errors` | Field-level validation or conflict details. |
| `retry_after_seconds` | Retry guidance for rate limits or dependency failures when known. |

Stable error codes:

| HTTP status | Code | When used |
| --- | --- | --- |
| `400` | `BAD_REQUEST` | Malformed JSON, invalid query syntax, or inconsistent request shape that is not field validation. |
| `401` | `UNAUTHENTICATED` | Missing, invalid, expired, or revoked credentials. Include `WWW-Authenticate` when useful. |
| `403` | `AUTHORIZATION_DENIED` | Authenticated actor is not allowed to perform a known operation. |
| `404` | `NOT_FOUND` | Resource does not exist or must be hidden from the actor to avoid existence disclosure. |
| `409` | `CONFLICT` | Idempotency mismatch, duplicate unique value, state conflict, or unsupported lifecycle transition. |
| `422` | `VALIDATION_FAILED` | Request body/params are syntactically valid but fail schema or domain validation. |
| `429` | `RATE_LIMITED` | Rate limit exceeded. |
| `500` | `INTERNAL_ERROR` | Unexpected server failure. |
| `503` | `SERVICE_UNAVAILABLE` | Required dependency unavailable, including readiness check failure. |

Security rules:

| Rule | Requirement |
| --- | --- |
| Unauthorized reads | Detail and mutation targets that are inaccessible return `404 NOT_FOUND`; still emit `authorization.denied`. |
| Error details | Do not reveal whether another tenant's resource exists. |
| Validation errors | Field errors may name invalid fields, but must not echo secret values. |
| Client branching | Clients branch on HTTP status and `code`, not `detail`. |

Endpoint-level status rules:

| Case | HTTP status | Code |
| --- | --- | --- |
| Successful create | `201` | None |
| Successful read/update/action | `200` | None |
| Successful delete/revoke with no body | `204` | None |
| CLI token polling still pending | `200` | None; body status is `authorization_pending`. |
| Malformed cursor, malformed JSON, unsupported query shape | `400` | `BAD_REQUEST` |
| Missing, invalid, expired, or revoked auth | `401` | `UNAUTHENTICATED` |
| Authenticated actor lacks permission on a readable resource | `403` | `AUTHORIZATION_DENIED` |
| Resource does not exist or is hidden from actor | `404` | `NOT_FOUND` |
| Duplicate unique value, idempotency mismatch, invalid lifecycle state, or duplicate grant | `409` | `CONFLICT` |
| Schema/domain validation failure | `422` | `VALIDATION_FAILED` |

## Pagination Contract

List-like endpoints use keyset pagination from v1.

Request parameters:

| Parameter | Requirement |
| --- | --- |
| `limit` | Optional page size. Default `50`. Maximum `100`. Endpoints may use lower defaults for expensive queries. |
| `cursor` | Optional opaque cursor returned by the previous response. |

Response field:

```json
{
  "page": {
    "next_cursor": "eyJ2IjoxLCJrIjpb...",
    "has_more": true
  }
}
```

Cursor rules:

| Rule | Requirement |
| --- | --- |
| Opaque | Clients must not parse or construct cursors. |
| Stable order | Every paginated endpoint must define deterministic ordering with a unique tie-breaker such as `id`. |
| No total count | Do not return `total_count` in v1; it can be expensive and misleading under authorization filters. |
| Filter consistency | Cursor encodes or validates the filter/sort context so it cannot be reused with different filters silently. |
| Invalid cursor | Return `400 BAD_REQUEST` with code `BAD_REQUEST`. |

Initial sort orders:

| Endpoint | Sort order |
| --- | --- |
| Memory list | `updated_at desc, id desc`. |
| Review queue | `created_at asc, id asc` to process oldest proposals first. |
| Search | `score desc, updated_at desc, id desc`. |
| Project timeline | `timestamp desc, id desc`. |
| Admin lists | `created_at desc, id desc` unless the endpoint defines a more useful sort. |

## Endpoint Summary

### Public And Auth Endpoints

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/health` | Basic liveness check. | None |
| GET | `/health/live` | Process liveness check. | None |
| GET | `/health/ready` | Dependency readiness check. | None |
| GET | `/v1/auth/providers` | List configured login providers. | None |
| POST | `/v1/auth/cli/authorizations` | Start CLI browser login. | None |
| GET | `/v1/auth/cli/authorizations/{user_code}` | Browser verification page for CLI login. | None, then OIDC |
| GET | `/v1/auth/oidc/{provider}/authorize` | Start OIDC login for UI or CLI verification. | None |
| GET | `/v1/auth/oidc/{provider}/callback` | Complete OIDC login. | Provider callback |
| POST | `/v1/auth/cli/token` | Exchange authorized CLI login for Nexus credentials. | None with one-time device code |
| POST | `/v1/auth/session/refresh` | Rotate refresh token and issue a new access token. | Refresh token |
| POST | `/v1/auth/session/revoke` | Revoke current session. | Access or refresh token |
| GET | `/v1/auth/me` | Return current actor and session context. | `auth:read` if restricted |
| GET | `/v1/auth/sessions` | List own active sessions. | `auth:sessions:manage` if restricted |
| DELETE | `/v1/auth/sessions/{session_id}` | Revoke one own session. | `auth:sessions:manage` if restricted |

### Product Endpoints

| Method | Path | Purpose | Required session capability if restricted |
| --- | --- | --- | --- |
| GET | `/v1/memory-entries` | List/browse authorized memory. | `memory:read` |
| POST | `/v1/memory-entries` | Create one memory entry. | `memory:create` |
| POST | `/v1/memory-entries:bulk` | Create multiple independent memory entries. | `memory:create` |
| GET | `/v1/memory-entries/{id}` | Read one authorized memory entry. | `memory:read` |
| PATCH | `/v1/memory-entries/{id}` | Edit an authorized memory entry. | `memory:update` |
| POST | `/v1/memory-entries/{id}/review` | Approve, reject, or reconfirm memory. | `memory:review` |
| POST | `/v1/memory-entries/{id}/mark-needs-review` | Mark active memory as needing review. | `memory:review` |
| POST | `/v1/memory-entries/{id}/deprecate` | Mark active or needs-review memory as deprecated. | `memory:review` |
| POST | `/v1/memory-entries/{id}/archive` | Archive memory. | `memory:update` |
| DELETE | `/v1/memory-entries/{id}` | Soft-delete eligible memory. | `memory:update` |
| PATCH | `/v1/memory-entries/{id}/visibility` | Change visibility. | `memory:update` |
| POST | `/v1/memory-entries/{id}/grants` | Add restricted memory grant. | `grants:manage` |
| DELETE | `/v1/memory-entries/{id}/grants/{grant_id}` | Remove restricted memory grant. | `grants:manage` |
| GET | `/v1/review-queue` | List memory the actor can review. | `memory:review` |
| POST | `/v1/search` | Search authorized memory. | `search:read` |
| POST | `/v1/context-packs` | Generate authorized context pack. | `context_pack:generate` |
| GET | `/v1/projects/{project_id}/timeline` | Read authorized project memory timeline. | `memory:read` |

### Admin Endpoints

Admin endpoints require `org_memberships.is_org_admin = true`. If the auth session is restricted, it must also include `admin:manage`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/v1/admin/users` | List organization users. |
| POST | `/v1/admin/users` | Create or pre-provision a user record. |
| GET | `/v1/admin/users/{user_id}` | Read user admin details. |
| PATCH | `/v1/admin/users/{user_id}` | Update display name or status. |
| GET | `/v1/admin/org-memberships` | List organization memberships and roles. |
| PUT | `/v1/admin/org-memberships/{user_id}` | Set a user's organization knowledge role and admin capability. |
| GET | `/v1/admin/groups` | List groups. |
| POST | `/v1/admin/groups` | Create group. |
| GET | `/v1/admin/groups/{group_id}` | Read group. |
| PATCH | `/v1/admin/groups/{group_id}` | Update group metadata or parent. |
| GET | `/v1/admin/groups/{group_id}/memberships` | List group memberships. |
| PUT | `/v1/admin/groups/{group_id}/memberships/{user_id}` | Set group member role. |
| DELETE | `/v1/admin/groups/{group_id}/memberships/{user_id}` | Remove group membership. |
| GET | `/v1/admin/projects` | List projects. |
| POST | `/v1/admin/projects` | Create project. |
| GET | `/v1/admin/projects/{project_id}` | Read project. |
| PATCH | `/v1/admin/projects/{project_id}` | Update project metadata, owning group, or status. |
| GET | `/v1/admin/projects/{project_id}/memberships` | List explicit project memberships. |
| PUT | `/v1/admin/projects/{project_id}/memberships/{user_id}` | Set explicit project role. |
| DELETE | `/v1/admin/projects/{project_id}/memberships/{user_id}` | Remove explicit project membership. |

Admin behavior:

| Rule | Requirement |
| --- | --- |
| No memory bypass | `is_org_admin = true` does not read private/restricted memory unless normal memory authorization allows it. |
| No approval by admin alone | `is_org_admin = true` does not approve organization-scoped memory unless `role = knowledge_admin`. |
| Org membership changes | Changing `role` or `is_org_admin` is audited and cannot remove the last `is_org_admin = true` membership. |
| Self role changes | A user cannot remove or downgrade their own last administrative access through normal API flows. |
| Project membership | `is_org_admin = true` may configure project memberships; project `maintainer` may configure memberships for that project if future UI enables project-local admin. |
| Group membership | `is_org_admin = true` may configure group memberships; group `lead` may manage group membership only if a later spec explicitly grants it. |
| Audit | User, role, group, project, and membership mutations emit admin audit events. |

Organization membership update request:

```json
{
  "role": "knowledge_admin",
  "is_org_admin": true
}
```

Rules:

| Rule | Requirement |
| --- | --- |
| `role` | Must be `member` or `knowledge_admin`. |
| `is_org_admin` | Boolean admin capability. |
| Last admin | Request is rejected with `409 CONFLICT` if it would remove the last organization admin. |
| Self-downgrade | Request is rejected with `409 CONFLICT` if it would remove the actor's last admin path. |

## Healthcheck

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "nexus-api",
  "version": "0.1.0",
  "time": "2026-06-28T12:00:00Z"
}
```

Behavior:

| Endpoint | Requirement |
| --- | --- |
| `/health` | Lightweight liveness response. No auth. No dependency details. |
| `/health/live` | Same liveness semantics for process supervisors. |
| `/health/ready` | Checks required dependencies such as PostgreSQL. Return `503 SERVICE_UNAVAILABLE` when not ready. |

## OIDC And CLI Login

The initial product supports Google SSO only. The only provider id required in v1 is `google`.

### List Providers

```http
GET /v1/auth/providers
```

Response:

```json
{
  "providers": [
    {
      "id": "google",
      "label": "Google",
      "type": "oidc"
    }
  ]
}
```

### Start CLI Login

```http
POST /v1/auth/cli/authorizations
```

Request:

```json
{
  "client_name": "nexus-cli",
  "requested_capabilities": [
    "memory:create",
    "memory:read",
    "memory:update",
    "search:read",
    "context_pack:generate"
  ],
  "max_visibility_scope": "project"
}
```

Response:

```json
{
  "device_code": "dev_01J...",
  "user_code": "ABCD-EFGH",
  "verification_uri": "https://nexus.example.com/v1/auth/cli/authorizations/ABCD-EFGH",
  "expires_in": 600,
  "interval": 5
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Browser SSO | CLI opens `verification_uri`; user completes Google/OIDC login in browser. |
| Pending login | `device_code` is one-time and expires quickly. Store only a hash. |
| Capabilities | Requested capabilities become session restrictions after approval. They never expand user permissions. |
| Max visibility | Requested `max_visibility_scope` caps create/visibility expansion for this session. |

State machine:

| From | Event | To | HTTP behavior |
| --- | --- | --- | --- |
| none | CLI starts authorization | `pending` | `201` with device code and verification URI. |
| `pending` | CLI polls before approval | `pending` | `200` with `authorization_pending`. |
| `pending` | User completes Google SSO | `approved` | Browser flow shows success. |
| `pending` | User/system denies | `denied` | Token exchange returns `403 AUTHORIZATION_DENIED`. |
| `pending` | Expiry time passes | `expired` | Token exchange returns `400 BAD_REQUEST` with safe detail. |
| `approved` | CLI exchanges device code | `exchanged` | `200` with Nexus credentials. |
| `exchanged` | CLI reuses device code | `exchanged` | `409 CONFLICT`. |

### Exchange CLI Login

```http
POST /v1/auth/cli/token
```

Request while polling:

```json
{
  "device_code": "dev_01J..."
}
```

Pending response:

```json
{
  "status": "authorization_pending",
  "interval": 5
}
```

Successful response:

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "nxs_rt_...",
  "refresh_expires_in": 43200,
  "session_id": "33333333-3333-4333-8333-333333333333",
  "org_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "user_id": "44444444-4444-4444-8444-444444444444",
  "capabilities": ["memory:create", "memory:read", "search:read"],
  "max_visibility_scope": "project"
}
```

### Refresh Session

```http
POST /v1/auth/session/refresh
```

Request:

```json
{
  "refresh_token": "nxs_rt_..."
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Rotation | Refresh token is single-use and rotated on every refresh. |
| Storage | Store only refresh token hash. |
| Reuse detection | Reusing an old refresh token revokes the session and emits a security audit event. |
| User state | Disabled users cannot refresh sessions. |

### Session Claims

Nexus access tokens must include enough claims to validate the session and resolve the actor:

| Claim | Requirement |
| --- | --- |
| `iss` | Nexus issuer. |
| `aud` | Nexus API audience. |
| `sub` | User id. |
| `org_id` | Organization id. |
| `sid` | Auth session id. |
| `client_type` | `web`, `cli`, or future client type. |
| `capabilities` | Session capabilities. Empty or omitted means unrestricted session capabilities; user permissions still apply. |
| `max_visibility_scope` | Optional visibility cap for create/visibility expansion. |
| `iat`, `exp`, `auth_time` | Standard issuance, expiry, and authentication timestamps. |

## Create Memory

```http
POST /v1/memory-entries
```

Request:

```json
{
  "project_id": "11111111-1111-4111-8111-111111111111",
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
  "id": "22222222-2222-4222-8222-222222222222",
  "status": "pending_review",
  "visibility_scope": "project",
  "requires_review": true
}
```

Response when actor is project reviewer or maintainer:

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
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
| Session attribution | Store `submitted_via_session_id` when request uses an auth session. |
| Idempotency | If `client_entry_id` matches existing unique key for actor/source tool, return existing entry instead of duplicating. |
| Evidence | Create evidence rows in same transaction. |
| Confidence | Validate `confidence is null or confidence between 0 and 1`. |
| Search vector | Update search vector after create. |
| Audit | Emit `memory_entry.created`. |

## Create Bulk Memory

```http
POST /v1/memory-entries:bulk
```

Bulk creates multiple independent memory entries. It does not create a batch entity.

Behavior:

| Rule | Requirement |
| --- | --- |
| Entry independence | Each entry has its own status, evidence, and audit behavior. |
| No capture batch | Do not add a batch table or batch resource. |
| Idempotency | Apply per-entry idempotency when `client_entry_id` is present. |
| Atomicity | v1 is all-or-nothing: validate authorization and schema for every entry before persisting; any invalid entry fails the whole request. |
| Transaction | All created entries, evidence, search-vector updates, and audit events are committed in one transaction. |

## List Memory

```http
GET /v1/memory-entries?project_id=11111111-1111-4111-8111-111111111111&type=decision&tag=payments&limit=50&cursor=...
```

Query filters:

| Filter | Requirement |
| --- | --- |
| `project_id` | Restrict to memory associated to a project without bypassing visibility. |
| `type` | Repeatable memory type filter. |
| `status` | Repeatable status filter. Hidden statuses require explicit authorized mode. |
| `tag` | Repeatable tag filter. |
| `source_tool` | Filter by source tool. |
| `owner_user_id` | Filter by owner. |
| `visibility_scope` | Filter by visibility scope. |
| `from`, `to` | Filter by updated timestamp unless endpoint later defines created timestamp. |
| `limit`, `cursor` | Keyset pagination. |

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Use `readable_memory_entries(actor)`. |
| Default statuses | `active` and `needs_review`. |
| Hidden statuses | `pending_review`, `rejected`, `deprecated`, and `archived` require explicit authorized mode. |
| UI support | This endpoint backs the Project Memory browse view. |

## Read Memory

```http
GET /v1/memory-entries/{id}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Use `readable_memory_entries(actor)`. |
| Denial | Unauthorized detail reads return `404 NOT_FOUND` and are audited. |
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
| Active shared edits | Only actors with control over the shared memory may edit active shared memory and keep it `active`. |
| Non-controller edits | Non-controller edits to active shared memory are denied; create a new proposal instead of silently rewriting approved truth. |
| Search vector | Update search vector after content/tag/rationale changes. |
| Audit | Emit `memory_entry.updated`. |

Patch semantics:

| Field class | Semantics |
| --- | --- |
| Omitted field | Leave unchanged. |
| Nullable scalar sent as `null` | Clear the field if the field is mutable and nullable. |
| `tags` array | Replace the full array. |
| `metadata` object | Replace the full object. |
| `source_context` object | Replace the full object only when the edit policy allows source metadata edits. |
| Immutable fields | `id`, `org_id`, `owner_user_id`, `created_by_user_id`, `submitted_via_session_id`, `created_at`, and `deleted_at` are not patchable. |

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

Self-review is denied with `403 AUTHORIZATION_DENIED` when the reviewer is the owner or creator of the shared memory.

## Review Queue

```http
GET /v1/review-queue?project_id=11111111-1111-4111-8111-111111111111&status=pending_review&limit=50&cursor=...
```

Filters:

| Filter | Requirement |
| --- | --- |
| `project_id` | Restrict to reviewable project memory. |
| `visibility_group_id` | Restrict to reviewable group memory. |
| `visibility_scope` | Restrict to `group`, `project`, or `organization`. |
| `status` | Defaults to `pending_review`; `needs_review` may be requested. |
| `type` | Repeatable memory type filter. |
| `owner_user_id` | Filter by proposer/owner. |
| `source_tool` | Filter by source tool. |
| `limit`, `cursor` | Keyset pagination. |

Response:

```json
{
  "items": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "type": "decision",
      "title": "Payment sync retries must use idempotency keys",
      "body": "Concurrent retries must use idempotency keys.",
      "rationale": "Found during duplicate event debugging.",
      "status": "pending_review",
      "visibility_scope": "project",
      "project_id": "11111111-1111-4111-8111-111111111111",
      "owner_user_id": "44444444-4444-4444-8444-444444444444",
      "source_tool": "codex",
      "confidence": 0.87,
      "evidence_count": 1,
      "created_at": "2026-06-28T12:00:00Z"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Return only memory the actor can review/reconfirm. |
| Default status | `pending_review`. |
| Needs review | Include `needs_review` only when explicitly requested and actor can review it. |
| No general read bypass | Review queue can expose pending items only to valid reviewers for that scope. |

## Lifecycle Endpoints

### Mark Needs Review

```http
POST /v1/memory-entries/{id}/mark-needs-review
```

Request:

```json
{
  "reason": "Needs reconfirmation after payment provider change."
}
```

Behavior: move `active` memory to `needs_review`, set warning metadata if implemented, emit `memory_entry.marked_needs_review`.

### Deprecate

```http
POST /v1/memory-entries/{id}/deprecate
```

Request:

```json
{
  "reason": "Superseded by the new webhook retry design."
}
```

Behavior: move `active` or `needs_review` memory to `deprecated`, emit `memory_entry.deprecated`.

### Archive

```http
POST /v1/memory-entries/{id}/archive
```

Request:

```json
{
  "reason": "No longer useful in normal workflows."
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Result | Move eligible memory to `archived`. |
| Purpose | Hide historical memory from normal list/search/context packs while retaining audit history. |
| Permission | Requires control over the memory scope. |
| Audit | Emit `memory_entry.archived`. |

### Soft Delete

```http
DELETE /v1/memory-entries/{id}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Result | Set `deleted_at`; do not hard delete in normal product flows. |
| Private/restricted | Owner or restricted memory manager may soft-delete. |
| Pending proposal | Owner may withdraw their own pending shared proposal. |
| Active shared memory | Normal `DELETE` is denied with `409 CONFLICT`; use archive instead. |
| Audit | Emit `memory_entry.deleted`. |

## Change Visibility

```http
PATCH /v1/memory-entries/{id}/visibility
```

Request:

```json
{
  "visibility_scope": "project",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "reason": "This decision is useful for the whole project."
}
```

Possible response:

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
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
| Session max visibility | Restricted sessions cannot create or expand beyond `max_visibility_scope`. |
| Audit | Emit `memory_entry.visibility_changed`. |

## Add Grant

```http
POST /v1/memory-entries/{id}/grants
```

Request:

```json
{
  "grantee_user_id": "55555555-5555-4555-8555-555555555555",
  "role": "viewer"
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Scope | Grants are for restricted memory and concrete users. |
| Duplicate | One grant per memory/user pair; duplicate add returns `409 CONFLICT`. |
| Roles | `viewer` reads, `editor` reads/edits, `manager` reads/edits/manages grants and may archive/delete restricted memory. |
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
  "project_id": "11111111-1111-4111-8111-111111111111",
  "types": ["decision", "problem", "solution", "failed_attempt"],
  "statuses": ["active", "needs_review"],
  "tags": ["payments"],
  "limit": 10,
  "cursor": null,
  "include_evidence": true
}
```

Response:

```json
{
  "results": [
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "type": "decision",
      "title": "Payment sync retries must use idempotency keys",
      "body": "Concurrent retries must use idempotency keys to avoid duplicate processing.",
      "status": "active",
      "visibility_scope": "project",
      "project_id": "11111111-1111-4111-8111-111111111111",
      "tags": ["payments", "sync", "idempotency"],
      "score": 0.91,
      "evidence_count": 1
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}
```

## Context Pack

```http
POST /v1/context-packs
```

Request:

```json
{
  "project_id": "11111111-1111-4111-8111-111111111111",
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
  "project_id": "11111111-1111-4111-8111-111111111111",
  "generated_at": "2026-06-28T12:00:00Z",
  "items": {
    "decisions": [
      {
        "id": "22222222-2222-4222-8222-222222222222",
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
GET /v1/projects/{project_id}/timeline?from=2026-06-01T00:00:00Z&to=2026-06-28T23:59:59Z&limit=50&cursor=...
```

Response:

```json
{
  "project_id": "11111111-1111-4111-8111-111111111111",
  "events": [
    {
      "timestamp": "2026-06-10T12:00:00Z",
      "event_type": "memory_entry.created",
      "memory_entry_id": "22222222-2222-4222-8222-222222222222",
      "type": "decision",
      "title": "Payment sync retries must use idempotency keys"
    },
    {
      "timestamp": "2026-06-12T09:00:00Z",
      "event_type": "memory_entry.approved",
      "memory_entry_id": "22222222-2222-4222-8222-222222222222"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  }
}
```

Behavior:

| Rule | Requirement |
| --- | --- |
| Authorization | Timeline only includes events for memory the actor can read. |
| Project scope | Use requested project. |
| Time range | Respect `from` and `to`. |
| Pagination | Use the common keyset pagination contract. |

## CLI Contract

CLI/plugin clients must:

| Requirement | Detail |
| --- | --- |
| Authenticate | Use `nexus login` to obtain short-lived session credentials through OIDC. |
| Store credentials safely | Store refresh credentials in OS keychain or the safest platform-available storage. |
| Refresh | Refresh access tokens through `/v1/auth/session/refresh`. |
| Submit structured entries | Send memory proposed by AI or user. |
| Include source tool | Set `source_tool`. |
| Include source ref | Set `source_ref` when available. |
| Include idempotency | Set `client_entry_id` where possible. |
| Include source context | Use flexible JSON metadata. |
| Respect review | Do not assume shared memory becomes active automatically. |
| Render locally | The CLI may render JSON/context packs as Markdown locally. |

Example future CLI:

```sh
nexus login
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

The API only returns structured data. Markdown rendering belongs in CLI/UI clients.
