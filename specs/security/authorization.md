# Authorization Spec

## Core Model

Only real users are permission actors in the product. AI tools such as Codex, OpenCode, Cursor, or ChatGPT are source tools. They act on behalf of a user through Nexus-issued session credentials created by OIDC login.

## Actor Context

Every authenticated request resolves an actor context:

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

## Authentication Requirements

| Method | Use |
| --- | --- |
| OIDC web session | UI/API direct calls. |
| OIDC CLI session | CLI/plugin/tool calls created by `nexus login`. |

Required headers:

```http
Authorization: Bearer <nexus_access_token>
X-Request-Id: <uuid>
```

`X-On-Behalf-Of` is not required in the product because session credentials already belong to a user.

## Session Credential Rules

| Rule | Requirement |
| --- | --- |
| Session identifies a user | Session is not an independent actor. |
| Session restricts permissions | Session capabilities intersect with user permissions. |
| Empty capabilities | Empty session capabilities mean no session-level capability restriction. |
| Session cannot raise visibility | `session_max_visibility_scope` caps creation and visibility expansion. |
| Session lifecycle enforced | Expired or revoked sessions are invalid. |
| User lifecycle enforced | Disabled users cannot authenticate, refresh, or use existing sessions. |
| Last use tracked | Successful session auth updates `last_used_at`. |
| Raw refresh token never stored | Store only refresh token hashes. |
| Refresh rotation | Refresh tokens are single-use and rotated on every refresh. |

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
deprecated
archived
```

Reviewers may query `pending_review` through explicit review endpoints only. `deprecated` and `archived` require explicit authorized modes.

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
| `GET /v1/memory-entries` | List/browse read. |
| `POST /v1/search` | Search. |
| `POST /v1/context-packs` | Context packs. |
| `GET /v1/projects/{project_id}/timeline` | Project timeline. |
| `GET /v1/review-queue` | Reviewable memory query, not normal readable query. |
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

Session `max_visibility_scope`, when set, must be checked before user role checks. A session may not create or expand memory above its maximum visibility even if the user would otherwise be allowed.

## Review Rules

| Scope | Who can approve/reject |
| --- | --- |
| `private` | No approval required. |
| `restricted` | No approval required. |
| `group` | `group.lead` of `visibility_group_id`. |
| `project` | Effective project `reviewer` or `maintainer`. |
| `organization` | `knowledge_admin`. |

## Admin Rules

`org_admin` is an organization configuration role. It is not a memory read or knowledge approval bypass.

| Operation | Requirement |
| --- | --- |
| Manage users | `org_admin`. |
| Enable/disable users | `org_admin`; disabling a user invalidates future session use and refresh. |
| Manage org roles | `org_admin`; cannot remove the last `org_admin`; self-downgrade is denied if it would remove the actor's last admin path. |
| Manage groups | `org_admin`. |
| Manage group memberships | `org_admin` in v1. Group lead management is future scope unless specified. |
| Manage projects | `org_admin`. |
| Manage project memberships | `org_admin` in v1. Project maintainer-local admin is future scope unless specified. |
| Approve organization memory | `knowledge_admin`; `org_admin` alone is insufficient. |
| Read private/restricted memory | Normal memory read rules only. `org_admin` has no bypass. |

Admin mutations must be audited. If a session is restricted, it also needs `admin:manage`.

## Edit Rules

| Case | Requirement |
| --- | --- |
| Private/restricted owner edit | Owner can edit. |
| Pending review owner edit | Owner can edit a pending entry they created. |
| Shared memory under review | Reviewer/maintainer can edit within their scope. |
| Active shared memory by controller | Actor with control over the memory scope may edit and keep it `active`. |
| Active shared memory by non-controller | Deny edit. The actor should create a new proposal instead of rewriting approved truth. |

Control over active shared memory means:

| Scope | Controller |
| --- | --- |
| `group` | `group.lead` for `visibility_group_id`. |
| `project` | Effective project `reviewer` or `maintainer`. |
| `organization` | `knowledge_admin`. |

For `private` and `restricted` memory, ownership and explicit grant roles control edit/manage behavior according to the restricted grant policy.

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

## Archive And Delete Rules

| Operation | Requirement |
| --- | --- |
| Archive private/restricted memory | Owner or restricted memory manager. |
| Archive group memory | Group lead. |
| Archive project memory | Effective project reviewer or maintainer. |
| Archive organization memory | `knowledge_admin`. |
| Soft-delete private/restricted memory | Owner or restricted memory manager. |
| Withdraw pending shared proposal | Owner may soft-delete their own pending proposal. |
| Soft-delete active shared memory | Denied in normal product flows; archive instead. |

Archive keeps historical memory with status `archived`. Soft delete sets `deleted_at` and excludes the row from all normal reads.

## Denial Rules

Every authorization denial must create an `authorization.denied` audit event with request context and safe metadata. Do not include secrets or raw sensitive bodies in audit metadata.

## Implementation Services

AuthorizationService must provide at least:

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
