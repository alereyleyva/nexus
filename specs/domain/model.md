# Domain Model Spec

## Domain Summary

Nexus stores independent memory entries inside an organization. A memory entry always belongs to an organization, may optionally reference a project, has an owner user, has a visibility scope, has a lifecycle status, may have evidence, and records source metadata from the client/tool that submitted it.

## Conceptual Diagram

```text
Organization
|-- Users
|-- Groups / Teams
|   |-- Projects owned by group
|-- Projects
|   |-- Memory entries associated to project
|-- Memory entries not associated to any project

User
|-- Auth sessions
|-- Org membership
|-- Group memberships
|-- Project memberships
|-- Owned memory entries

Memory Entry
|-- Organization: required
|-- Project: optional
|-- Owner user: required
|-- Visibility: private / restricted / group / project / organization
|-- Status: pending_review / active / needs_review / rejected / deprecated / archived
|-- Evidence: optional but recommended
|-- Source context: flexible JSON metadata
```

## Entity Responsibilities

| Entity | Responsibility |
| --- | --- |
| Organization | Tenant boundary, container for users, groups, projects, memory, and audit. |
| User | Real human actor for permissions, ownership, creation, review, and approval. |
| Org Membership | User role inside an organization. |
| Group | Team, department, squad, or area. Mainly team in the product scope. |
| Group Membership | User membership in a group with member or lead role. |
| Project | Product, service, initiative, or work area owned by one group. |
| Project Membership | Explicit project access for collaborators outside or above inherited group access. |
| Auth Session | Revocable user session created by UI or CLI login. |
| Auth CLI Authorization | Short-lived one-time browser approval record for `nexus login`. |
| Auth Refresh Token | Opaque rotated credential for renewing a session. |
| Memory Entry | Central knowledge unit. |
| Memory Entry Evidence | Supporting evidence attached to a memory entry. |
| Memory Entry Grant | Explicit user grant for restricted memory. |
| Audit Event | Operational audit record for sensitive operations and denials. |
| Context Pack | Non-persistent structured response grouping authorized memory for a task. |

## Required Relationships

| Relationship | Rule |
| --- | --- |
| Organization to users | One organization has many users. |
| Organization to groups | One organization has many groups. |
| Organization to projects | One organization has many projects. |
| Organization to memory entries | One organization has many memory entries. |
| Group to projects | One group owns many projects. |
| Project to owning group | Each project must have exactly one `owning_group_id`. |
| Project to memory entries | A memory entry may reference one project. |
| User to memory entries | Each memory entry has an owner and creator user. |
| User to auth sessions | A user may have many active or historical auth sessions. |
| Auth session to refresh tokens | A session may have many historical refresh token records due to rotation. |
| Memory entry to evidence | A memory entry may have many evidence rows. |
| Memory entry to grants | Restricted memory may have many explicit user grants. |

## Tenant Isolation

Every tenant-owned table must include `org_id`. Cross-organization relationships must be prevented through composite foreign keys where practical.

## Organization

| Field | Requirement |
| --- | --- |
| `id` | UUID primary key. |
| `slug` | Unique organization slug. |
| `name` | Display name. |
| `created_at`, `updated_at` | Timestamps. |

## User

| Field | Requirement |
| --- | --- |
| `id` | UUID primary key. |
| `org_id` | Required tenant reference. |
| `email` | Unique inside org. |
| `display_name` | Required human name. |
| `status` | `active` or `disabled`. |

Only active users are valid actors for normal authenticated operations.

## Org Membership

Organization administration and organization knowledge approval are separate capabilities in v1. This avoids role-set complexity while preserving least privilege.

Fields:

| Field | Requirement |
| --- | --- |
| `role` | Knowledge role: `member` or `knowledge_admin`. |
| `is_org_admin` | Boolean organization configuration capability. |

Knowledge roles:

| Role | Meaning |
| --- | --- |
| `member` | Normal organization user. |
| `knowledge_admin` | Can approve organization-scoped memory. |

Admin capability:

| Capability | Meaning |
| --- | --- |
| `is_org_admin = true` | Can manage users, organization memberships, groups, projects, and memberships. Does not automatically read private memory or approve organization-scoped memory. |

A user may be `member` with `is_org_admin = true`, `knowledge_admin` with `is_org_admin = false`, both, or neither.

## Group

| Field | Requirement |
| --- | --- |
| `id` | UUID primary key. |
| `org_id` | Required tenant reference. |
| `slug` | Unique inside org. |
| `name` | Display name. |
| `group_type` | `team`, `department`, `squad`, or `area`. |
| `parent_group_id` | Optional hierarchy reference. |

`parent_group_id` is visual/organizational only in the product scope. It must not grant inherited permissions until explicitly designed.

## Group Membership

| Role | Meaning |
| --- | --- |
| `member` | Can read group-visible memory. In owning group projects, derives project `contributor`. |
| `lead` | Can approve group memory. In owning group projects, derives project `maintainer`. |

## Project

| Field | Requirement |
| --- | --- |
| `id` | UUID primary key. |
| `org_id` | Required tenant reference. |
| `owning_group_id` | Required group owner. |
| `key` | Unique key inside org. |
| `name` | Display name. |
| `description` | Optional. |
| `status` | `active` or `archived`. |

Projects must not be orphaned. If ownership is unclear, assign a generic group such as Platform, Internal, or Unassigned.

## Project Membership

| Role | Can read | Can create/propose | Can approve | Can configure |
| --- | --- | --- | --- | --- |
| `viewer` | Yes | No | No | No |
| `contributor` | Yes | Yes | No | No |
| `reviewer` | Yes | Yes | Yes | No |
| `maintainer` | Yes | Yes | Yes | Yes |

## Effective Project Roles

| Source | Effective project role |
| --- | --- |
| `group.member` of owning group | `contributor` |
| `group.lead` of owning group | `maintainer` |
| Explicit project membership | Its configured role. |

If multiple roles apply, the highest role wins by this level order:

| Project role | Level |
| --- | --- |
| `viewer` | 10 |
| `contributor` | 20 |
| `reviewer` | 30 |
| `maintainer` | 40 |

## Auth Session

Auth sessions are revocable user sessions created by OIDC login. They are not actors. They restrict, never expand, user permissions.

The initial product login provider is Google OIDC. The auth module should keep provider logic behind an adapter boundary so future generic OIDC IdPs do not change memory authorization rules, but only Google is required in v1.

| Field | Requirement |
| --- | --- |
| `id` | UUID primary key. |
| `org_id` | Required tenant reference. |
| `user_id` | Required session user. |
| `provider` | OIDC provider id such as `google`. |
| `provider_subject` | Provider subject for the authenticated user. |
| `client_type` | `web`, `cli`, or future client type. |
| `client_name` | Optional human/client label such as `nexus-cli`. |
| `capabilities` | Optional session capability restrictions. Empty means no session-level capability restriction. |
| `max_visibility_scope` | Optional maximum visibility scope this session can create or expand to. |
| `expires_at`, `revoked_at`, `last_used_at` | Session lifecycle timestamps. |

Effective permissions are always:

```text
effective_permissions = user_permissions intersect session_capabilities intersect session_visibility_cap
```

If `capabilities` is empty, session capabilities do not restrict endpoint capability checks. User permissions and authorization rules still apply.

## Auth CLI Authorization

CLI login uses browser SSO instead of static API keys.

Lifecycle:

| Status | Meaning |
| --- | --- |
| `pending` | CLI created a device authorization and is polling. |
| `approved` | User completed Google SSO in browser and the authorization may be exchanged once. |
| `denied` | User or system denied the authorization. |
| `expired` | Authorization expired before exchange. |
| `exchanged` | CLI exchanged the authorization for Nexus session credentials. |

Fields:

| Field | Requirement |
| --- | --- |
| `device_code_hash` | Hash of one-time CLI device code. Store no raw code. |
| `user_code_hash` | Hash of browser verification code. Store no raw code. |
| `requested_capabilities` | Capabilities requested by CLI before user approval. |
| `max_visibility_scope` | Optional session visibility cap requested by CLI. |
| `client_name` | Human/client label such as `nexus-cli`. |
| `org_id`, `user_id` | Null while pending; set after successful Google SSO approval. |
| `approved_session_id` | Auth session created during exchange. |
| `expires_at`, `approved_at`, `exchanged_at` | Lifecycle timestamps. |

Rules:

| Rule | Requirement |
| --- | --- |
| One-time exchange | `approved` authorization may be exchanged once and then becomes `exchanged`. |
| Expiry | Expired authorizations cannot be approved or exchanged. |
| Storage | Store only code hashes. Do not audit or log raw codes. |
| Capabilities | Requested capabilities restrict the resulting CLI session and never expand user permissions. |

## Auth Refresh Token

Refresh tokens are opaque values returned only once to clients. Store only hashes.

| Field | Requirement |
| --- | --- |
| `id` | UUID primary key. |
| `org_id` | Required tenant reference. |
| `session_id` | Required auth session reference. |
| `token_hash` | Hash only; never store raw refresh token. |
| `parent_token_id` | Optional previous refresh token for rotation chain. |
| `expires_at`, `used_at`, `revoked_at` | Refresh token lifecycle timestamps. |

Refresh tokens are single-use. Reuse of an already used refresh token must revoke the session and emit a security audit event.

## Session Capabilities

| Capability | Meaning |
| --- | --- |
| `memory:create` | Create entries. |
| `memory:read` | Read allowed entries. |
| `memory:update` | Edit allowed entries. |
| `memory:review` | Review if user role also permits it. |
| `search:read` | Execute searches. |
| `context_pack:generate` | Generate context packs. |
| `grants:manage` | Manage grants for owned or administrable entries. |
| `admin:manage` | Use organization admin endpoints when the user also has `is_org_admin = true`. |
| `auth:read` | Read current auth context when sessions are restricted. |
| `auth:sessions:manage` | List and revoke own sessions when sessions are restricted. |

## Visibility Scope Order

```text
private < restricted < group < project < organization
```

## Memory Entry

| Field | Requirement |
| --- | --- |
| `org_id` | Required organization. |
| `project_id` | Optional project association. |
| `owner_user_id` | Required owner. |
| `created_by_user_id` | Required creator. |
| `submitted_via_session_id` | Optional auth session used by CLI/plugin. |
| `type` | One supported memory type. |
| `title` | Required. |
| `body` | Required. |
| `rationale` | Optional, recommended for decisions/problems/solutions. |
| `status` | One lifecycle status. |
| `visibility_scope` | One visibility scope. Defaults to `private` if omitted by client. |
| `visibility_group_id` | Required only for `group` visibility. |
| `source_kind` | `ai_cli`, `manual`, `api`, or `future_integration`. |
| `source_tool` | Free-text source tool name such as `codex`. |
| `source_ref` | Optional source thread/session/reference. |
| `client_entry_id` | Optional idempotency key from client. |
| `confidence` | Optional confidence value from client/tool. Must be null or between 0 and 1. Not an approval substitute. |
| `tags` | Text array. |
| `source_context` | Flexible JSONB source metadata. |
| `metadata` | Flexible JSONB implementation/product metadata. |
| `reviewed_by_user_id`, `review_comment`, `reviewed_at` | Review metadata. |
| `review_after` | Optional freshness review date. |
| `search_vector` | PostgreSQL FTS vector. |
| `deleted_at` | Soft delete timestamp. |

## Memory Types

| Type | Meaning | Example intent |
| --- | --- | --- |
| `decision` | Technical, functional, or organizational decision. | Capture what was decided and why. |
| `problem` | Detected issue. | Capture cause, impact, and context. |
| `solution` | Working solution. | Capture what worked and under what conditions. |
| `failed_attempt` | Tried and discarded option. | Prevent repeated work. |
| `procedure` | Reusable operational procedure. | Explain safe repeatable steps. |
| `risk` | Known risk. | Surface risk in context packs. |
| `open_question` | Unresolved question. | Track future decision need. |
| `task` | Derived action item. | Capture follow-up work. |
| `note` | General useful note. | Preserve informal context. |

## Memory Statuses

| Status | Meaning | Normal search | Normal context pack |
| --- | --- | --- | --- |
| `pending_review` | Awaiting human review before sharing. | No | No |
| `active` | Valid and usable. | Yes | Yes |
| `needs_review` | Visible but stale/doubtful warning required. | Yes, with warning | Yes, with warning |
| `rejected` | Rejected and should not be used. | No | No |
| `deprecated` | Was valid but not recommended. | Only if explicitly requested | No by default |
| `archived` | Historical, hidden by default. | Only if explicitly requested | No |

## Status Transitions

| From | Action | To |
| --- | --- | --- |
| `pending_review` | approve | `active` |
| `pending_review` | reject | `rejected` |
| `active` | mark_needs_review | `needs_review` |
| `needs_review` | approve/reconfirm | `active` |
| `active` | deprecate | `deprecated` |
| `active` | archive | `archived` |
| `deprecated` | archive | `archived` |

## Visibility Model

| Scope | Audience |
| --- | --- |
| `private` | Owner only. |
| `restricted` | Owner plus explicit user grants. |
| `group` | Members of `visibility_group_id`. |
| `project` | Effective project audience. |
| `organization` | Active members of the organization. |

## Visibility Constraints

| Constraint | Requirement |
| --- | --- |
| Private by default | Missing client visibility creates `private` memory. |
| Group visibility | Requires `visibility_group_id`. |
| Non-group visibility | Must not set `visibility_group_id`. |
| Project visibility | Requires `project_id`. |
| Project association | `project_id` alone never grants project visibility. |
| Organization admins | `is_org_admin = true` does not automatically read private memory owned by others. |

## Memory Entry Grant

Grants only apply to `restricted` memory and only to concrete users.

| Grant role | Meaning |
| --- | --- |
| `viewer` | Can read. |
| `editor` | Can read and edit where policy permits. |
| `manager` | Can manage sharing where policy permits. |

Do not use memory entry grants to model groups, projects, or organization visibility.

Grant permissions:

| Grant role | Read | Edit | Manage grants | Archive/delete |
| --- | --- | --- | --- | --- |
| `viewer` | Yes | No | No | No |
| `editor` | Yes | Yes | No | No |
| `manager` | Yes | Yes | Yes | Yes for restricted memory |

## Evidence

Evidence inherits memory visibility. It has no separate visibility in the product.

| Evidence kind | Meaning |
| --- | --- |
| `quote` | Text quote. |
| `code_reference` | Code location. |
| `document_reference` | Document reference. |
| `meeting_note` | Meeting note. |
| `chat_message` | Chat message. |
| `url` | URL. |
| `ticket` | Ticket reference. |
| `pull_request` | Pull request reference. |
| `commit` | Commit reference. |
| `manual_note` | Manual note. |

## Source Context

`source_context` is flexible JSONB. It stores origin details without creating rigid product entities such as repositories, meetings, documents, tickets, or sessions.

Code example:

```json
{
  "repository_url": "git@github.com:example-org/payments-platform.git",
  "branch": "fix/payment-sync-retries",
  "commit_sha": "abc123",
  "pull_request": 42,
  "files": [
    {
      "path": "services/payment_sync/retry_handler.py",
      "line_start": 82,
      "line_end": 116
    }
  ]
}
```

Meeting example:

```json
{
  "meeting_title": "Project handover planning",
  "meeting_date": "2026-06-28",
  "participants": ["morgan@company.com", "riley@company.com"]
}
```

Document example:

```json
{
  "document_title": "Architecture Notes",
  "document_url": "internal-docs://project-architecture",
  "section": "Payment sync"
}
```

Support example:

```json
{
  "customer": "ACME",
  "ticket_id": "SUP-1234",
  "area": "billing"
}
```

## Context Pack

A context pack is not persisted. It is a structured response that selects, groups, and returns authorized memory for a task. It does not call AI, summarize with LLMs, or create memory.
