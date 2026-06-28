# Internal Services Spec

## Service Overview

The product should keep business logic in explicit services. Routers should be thin. Repositories should not contain permission decisions except query helpers that are called by services.

## AuthService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Validate JWT | Resolve authenticated user for UI/API calls. |
| Validate API token | Hash/compare token, check expiration and revocation. |
| Resolve user | Load active user and organization context. |
| Update token usage | Set `last_used_at` on successful token auth. |
| Build actor context | Return `ActorContext`. |

Minimum actor context:

```python
class ActorContext(BaseModel):
    org_id: UUID
    user_id: UUID
    token_id: UUID | None
    token_scopes: set[str]
    token_max_visibility_scope: VisibilityScope | None
    request_id: str
```

## AuthorizationService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Resolve organization role | Determine `member`, `knowledge_admin`, or `org_admin`. |
| Resolve group memberships | Determine group IDs and group roles. |
| Resolve effective project role | Combine owning group inheritance and explicit project membership. |
| Validate creation | Return initial status and review requirement. |
| Validate read | Enforce visibility/status/org/deleted rules. |
| Validate edit | Enforce owner/reviewer/shared-memory edit rules. |
| Validate approval | Enforce reviewer/lead/knowledge admin rules. |
| Validate visibility change | Enforce target audience expansion rules. |
| Build readable query | Return base query for authorized memory reads. |

Key functions:

```python
can_read_memory(actor, memory) -> bool
can_create_memory(actor, payload) -> CreationDecision
can_review_memory(actor, memory) -> bool
can_change_visibility(actor, memory, target_visibility) -> VisibilityDecision
readable_memory_query(actor, statuses) -> Select
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
| Change visibility | Apply target-scope authorization and review status. |
| Manage grants | Add/remove restricted grants. |
| Archive/soft delete | Hide memory without hard delete. |
| Emit audit events | Audit create/update/review/visibility/grants/archive. |
| Update search vector | Maintain PostgreSQL FTS vector. |

## SearchService

Responsibilities:

| Responsibility | Requirement |
| --- | --- |
| Execute lexical search | Use PostgreSQL FTS. |
| Apply filters | Project, type, status, tags, limit. |
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
| Avoid secrets | Exclude raw tokens, secret-bearing bodies, raw search query by default. |
| Record denials | Persist `authorization.denied`. |

## Service Interaction Flows

Write flow:

```text
Client with user token
-> Nexus API
-> AuthService
-> AuthorizationService
-> MemoryEntryService
-> PostgreSQL
-> AuditService
```

Read/search/context pack flow:

```text
Client with user token
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
