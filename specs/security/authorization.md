# Authorization Spec

## Core Model

Only real users are permission actors in the product. AI tools such as Codex, OpenCode, Cursor, or ChatGPT are source tools. They act on behalf of a user through JWT or personal API token authentication.

## Actor Context

Every authenticated request resolves an actor context:

```python
class ActorContext(BaseModel):
    org_id: UUID
    user_id: UUID
    token_id: UUID | None
    token_scopes: set[str]
    token_max_visibility_scope: VisibilityScope | None
    request_id: str
```

## Authentication Requirements

| Method | Use |
| --- | --- |
| User JWT | UI/API direct calls. |
| Personal API token | CLI/plugin/tool calls. |

Required headers:

```http
Authorization: Bearer <token>
X-Request-Id: <uuid>
```

`X-On-Behalf-Of` is not required in the product because personal API tokens already belong to a user.

## Token Permission Rules

| Rule | Requirement |
| --- | --- |
| Token identifies a user | Token is not an independent actor. |
| Token restricts permissions | Token scopes intersect with user permissions. |
| Token cannot raise visibility | `max_visibility_scope` caps creation scope. |
| Token lifecycle enforced | Expired or revoked tokens are invalid. |
| Last use tracked | Successful token auth updates `last_used_at`. |
| Raw token never stored | Store only `token_hash`. |

Visibility order:

```text
private < restricted < group < project < organization
```

## Universal Read Rule

A memory entry is readable only if all conditions are true:

| Condition | Requirement |
| --- | --- |
| Same org | `memory_entries.org_id = actor.org_id`. |
| Not deleted | `deleted_at is null`. |
| Visible state | Status is allowed for the endpoint/query mode. |
| Visibility audience | Actor belongs to the audience defined by `visibility_scope`. |

Default visible statuses for normal GET/search/context packs:

```text
active
needs_review
```

Default hidden statuses:

```text
pending_review
rejected
archived
```

Reviewers may query `pending_review` through explicit review endpoints only.

## Visibility Read Rules

| Scope | Read rule |
| --- | --- |
| `private` | Actor user is `owner_user_id`. |
| `restricted` | Actor is owner or has explicit memory grant. |
| `group` | Actor is member of `visibility_group_id`. |
| `project` | Actor has an effective role in `project_id`. |
| `organization` | Actor is an active member of the organization. |

## Critical Read Path Rule

The exact same readable memory logic must be used by:

| Path | Requirement |
| --- | --- |
| `GET /v1/memory-entries/{id}` | Detail read. |
| `POST /v1/search` | Search. |
| `POST /v1/context-packs` | Context packs. |
| `GET /v1/projects/{project_id}/timeline` | Project timeline. |
| Future exports | Any export path. |
| Future vector search | Candidate IDs must be revalidated. |

No internal route may read memory without authorization.

## Conceptual Read Query

The implementation should centralize the equivalent of:

```sql
select me.*
from memory_entries me
where me.org_id = :org_id
  and me.deleted_at is null
  and me.status in ('active', 'needs_review')
  and (
    me.owner_user_id = :actor_user_id
    or exists (
      select 1
      from memory_entry_grants meg
      where meg.org_id = me.org_id
        and meg.memory_entry_id = me.id
        and meg.grantee_user_id = :actor_user_id
        and meg.role in ('viewer', 'editor', 'manager')
    )
    or (
      me.visibility_scope = 'group'
      and me.visibility_group_id in (:actor_group_ids)
    )
    or (
      me.visibility_scope = 'project'
      and me.project_id in (:actor_project_ids)
    )
    or (
      me.visibility_scope = 'organization'
      and :actor_is_active_org_member
    )
  );
```

The concrete SQL may differ, but behavior must not.

## Create Rules

| Target visibility | Who can create/propose | Initial status |
| --- | --- | --- |
| `private` | Any active org user. | `active` |
| `restricted` | Any active org user. | `active` |
| `group` | Group member. | `pending_review` for `member`, `active` for `lead`. |
| `project` | Effective project `contributor`, `reviewer`, or `maintainer`. | `pending_review` for `contributor`, `active` for `reviewer`/`maintainer`. |
| `organization` | Any active org member may propose. | `pending_review` for `member`, `active` for `knowledge_admin`. |

`org_admin` does not automatically approve organization memory unless also `knowledge_admin`.

## Review Rules

| Scope | Who can approve/reject |
| --- | --- |
| `private` | No approval required. |
| `restricted` | No approval required. |
| `group` | `group.lead` of `visibility_group_id`. |
| `project` | Effective project `reviewer` or `maintainer`. |
| `organization` | `knowledge_admin`. |

## Edit Rules

| Case | Requirement |
| --- | --- |
| Private/restricted owner edit | Owner can edit. |
| Pending review owner edit | Owner can edit a pending entry they created. |
| Shared memory under review | Reviewer/maintainer can edit within their scope. |
| Active shared memory by contributor | Must not silently edit active shared truth. |
| Active shared memory by reviewer/maintainer | May stay active if approver has permission. |
| Active shared memory by non-approver | Should move to `pending_review` when material shared content changes. |

## Visibility Change Rules

Changing visibility is sensitive because it can increase audience.

General rule:

```text
Increasing audience requires approval permission over the destination scope.
```

| Change | Requirement/result |
| --- | --- |
| `private` to `restricted` | Owner can do it. |
| `private` to `group` | Requires group lead or becomes `pending_review`. |
| `private` to `project` | Requires reviewer/maintainer or becomes `pending_review`. |
| `private` to `organization` | Requires knowledge admin or becomes `pending_review`. |
| `project` to `organization` | Requires knowledge admin. |
| `organization` to `private` | Requires administrative policy and strong audit event. |

## Denial Rules

Every authorization denial must create an `authorization.denied` audit event with request context and safe metadata. Do not include secrets or raw sensitive bodies in audit metadata.

## Implementation Services

AuthorizationService must provide at least:

```python
can_read_memory(actor, memory) -> bool
can_create_memory(actor, payload) -> CreationDecision
can_review_memory(actor, memory) -> bool
can_change_visibility(actor, memory, target_visibility) -> VisibilityDecision
readable_memory_query(actor, statuses) -> Select
get_effective_project_role(actor, project_id) -> ProjectRole | None
```
