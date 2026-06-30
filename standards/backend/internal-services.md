# Internal Services Spec

## Service Overview

The product should keep business logic in explicit services. Routers should be thin. Repositories should not contain permission decisions except query helpers that are called by services.

## AuthService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Start OIDC login | Build provider authorization requests for UI and CLI verification. |
| Complete OIDC login | Validate provider callback and map provider identity to a Nexus user. |
| Start CLI authorization | Create short-lived pending CLI login with a one-time device code. |
| Exchange CLI authorization | Issue Nexus access and refresh credentials after browser SSO completes. |
| Validate access JWT | Verify signature, issuer, audience, expiry, and session id. |
| Rotate refresh token | Hash/compare refresh token, enforce single use, rotate on refresh. |
| Resolve user | Load active user and organization context. |
| Update session usage | Set `last_used_at` on successful session auth. |
| Revoke sessions | Revoke current or selected user session. |
| Build actor context | Return `ActorContext`. |

Minimum actor context:

```python
class ActorContext(BaseModel):
    org_id: UUID
    user_id: UUID
    session_id: UUID
    session_capabilities: set[str]
    session_max_visibility_scope: VisibilityScope | None
    client_type: Literal["web", "cli", "future_integration"]
    request_id: str
```

## AdminService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Manage users | Create/pre-provision, enable, disable, and update user records. |
| Manage org memberships | Set organization role and enforce last-admin/self-downgrade safeguards. |
| Manage groups | Create/update groups and parent references. |
| Manage group memberships | Add/update/remove user memberships. |
| Manage projects | Create/update projects, owning group, and project status. |
| Manage project memberships | Add/update/remove explicit project memberships. |
| Enforce admin boundary | Require `is_org_admin = true`; never bypass memory read or review permissions. |
| Audit admin changes | Emit admin audit events for all membership/permission mutations. |

## AuthorizationService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Resolve organization membership | Determine knowledge role (`member` or `knowledge_admin`) and `is_org_admin`. |
| Resolve group memberships | Determine group IDs and group roles. |
| Resolve effective project role | Combine owning group inheritance and explicit project membership. |
| Validate creation | Return initial status and review requirement. |
| Validate read | Enforce visibility/status/org/deleted rules. |
| Validate edit | Enforce owner/reviewer/shared-memory edit rules. |
| Validate approval | Enforce reviewer/lead/knowledge admin rules. |
| Validate visibility change | Enforce target audience expansion rules. |
| Validate archive/delete | Enforce archive and soft-delete rules. |
| Validate admin | Enforce organization admin rules. |
| Build readable query | Return base query for authorized memory reads. |
| Build reviewable query | Return base query for memory the actor may review. |

Key functions:

```python
can_read_memory(actor, memory) -> bool
can_create_memory(actor, payload) -> CreationDecision
can_edit_memory(actor, memory, patch) -> bool
can_review_memory(actor, memory) -> bool
can_change_visibility(actor, memory, target_visibility) -> VisibilityDecision
can_archive_memory(actor, memory) -> bool
can_soft_delete_memory(actor, memory) -> bool
can_administer_organization(actor) -> bool
readable_memory_query(actor, statuses) -> Select
reviewable_memory_query(actor, statuses) -> Select
get_effective_project_role(actor, project_id) -> ProjectRole | None
```

## MemoryEntryService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Create memory | Apply defaults, validate authz, persist memory. |
| Create evidence | Persist evidence in same transaction. |
| Apply initial status | Use authorization decision. |
| Edit memory | Apply edit policy and refresh search vector. |
| Review memory | Approve/reject/reconfirm and set review metadata. |
| Build review queue | Return paginated pending/needs-review memory the actor can review. |
| Mark needs review | Move active memory to `needs_review`. |
| Deprecate memory | Move active/needs-review memory to `deprecated`. |
| Change visibility | Apply target-scope authorization and review status. |
| Manage grants | Add/remove restricted grants. |
| Archive memory | Move eligible memory to `archived`. |
| Soft delete memory | Set `deleted_at` for eligible memory. |
| Emit audit events | Audit create/update/review/visibility/grants/archive/delete/status changes. |
| Update search vector | Maintain PostgreSQL FTS vector. |

## SearchService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Execute lexical search | Use PostgreSQL FTS. |
| Apply filters | Project, type, status, tags, limit, cursor. |
| Use readable query | Start from authorized memory only. |
| Rank results | Apply text rank, freshness, type priority, status score. |
| Include evidence | Include evidence count/details when requested. |
| Audit search | Emit `search.executed` without raw query by default. |

## ContextPackService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Select authorized memory | Use readable query/search behavior. |
| Group by type | Return decisions, problems, solutions, failed attempts, risks, procedures, open questions. |
| Limit items | Respect `max_items`. |
| Include warnings | Warn for `needs_review`. |
| Audit generation | Emit `context_pack.generated`. |
| Avoid persistence | Do not store context packs in the product. |
| Avoid AI calls | Do not call LLMs or summarize. |

## AuditService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Create audit events | Persist operation events. |
| Normalize metadata | Store safe structured metadata. |
| Avoid secrets | Exclude raw access/refresh tokens, secret-bearing bodies, raw search query by default. |
| Record denials | Persist `authorization.denied`. |

## Common API Services

| Service | Requirement |
| --- | --- |
| Error handling | Convert all API errors to the Problem Details envelope from `specs/api/rest-api.md`. |
| Pagination | Encode/decode opaque keyset cursors and validate filter consistency. |
| Request IDs | Read or generate request ids and include them in logs, audit, and error responses. |

## Service Interaction Flows

Write flow:

```text
Client with Nexus access token
-> Nexus API
-> AuthService
-> AuthorizationService
-> MemoryEntryService
-> PostgreSQL
-> AuditService
```

Read/search/context pack flow:

```text
Client with Nexus access token
-> Nexus API
-> AuthService
-> readable_memory_entries(actor)
-> SearchService or ContextPackService
-> PostgreSQL
-> AuditService
```

Fundamental rule:

```text
Every result returned to a client must have passed through readable_memory_entries(actor).
```
