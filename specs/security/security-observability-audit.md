# Security, Observability, And Audit Spec

## Security Baseline

| Rule | Requirement |
| --- | --- |
| TLS | Use TLS in transit. |
| Encryption at rest | Use PostgreSQL/storage encryption if infrastructure offers it. |
| Secret management | Keep secrets out of the repository. |
| Credential storage | Store refresh token hashes only; never store raw access or refresh tokens. |
| Soft delete | Use soft delete for memory entries. |
| Sensitive changes | Audit visibility, review, grants, denial, session lifecycle, admin mutations, search, and context pack generation. |
| Default private | New entries default to private visibility. |
| Org isolation | Use `org_id` in tenant-owned tables. |
| Cross-org safety | Use composite foreign keys where practical. |
| API boundary | No direct DB/search/vector access by clients. |

## Out Of Scope

| Capability | Status |
| --- | --- |
| Field-level encryption | Future enterprise capability. |
| KMS per organization | Future enterprise capability. |
| Break-glass access | Future enterprise capability with strong audit. |
| Complex retention policies | Future. |
| Automatic redaction pipeline | Future. |
| Automatic DLP | Future. |

## Audit Events

| Event | When emitted |
| --- | --- |
| `memory_entry.created` | Memory entry created. |
| `memory_entry.updated` | Memory entry edited. |
| `memory_entry.approved` | Memory entry approved. |
| `memory_entry.rejected` | Memory entry rejected. |
| `memory_entry.visibility_changed` | Visibility changed. |
| `memory_entry.grant_added` | Grant added. |
| `memory_entry.grant_removed` | Grant removed. |
| `memory_entry.marked_needs_review` | Memory marked needs review. |
| `memory_entry.deprecated` | Memory deprecated. |
| `memory_entry.archived` | Memory archived. |
| `memory_entry.deleted` | Memory soft-deleted. |
| `search.executed` | Search executed. |
| `context_pack.generated` | Context pack generated. |
| `authorization.denied` | Access denied. |
| `auth.session.created` | Auth session created after OIDC login. |
| `auth.session.refreshed` | Refresh token rotated and access token issued. |
| `auth.session.revoked` | Auth session revoked. |
| `auth.refresh_reuse_detected` | Used refresh token was reused and session was revoked. |
| `admin.user_changed` | User record created or changed. |
| `admin.org_membership_changed` | Organization role changed. |
| `admin.group_changed` | Group created or changed. |
| `admin.group_membership_changed` | Group membership changed. |
| `admin.project_changed` | Project created or changed. |
| `admin.project_membership_changed` | Project membership changed. |

## Audit Event Data

Each audit event includes:

| Field | Requirement |
| --- | --- |
| `org_id` | Required organization. |
| `actor_user_id` | Acting user if known. |
| `actor_session_id` | Auth session id when request is authenticated. |
| `action` | Event name. |
| `resource_type` | Resource type when applicable. |
| `resource_id` | Resource ID when applicable. |
| `decision` | `allow` or `deny` when applicable. |
| `reason` | Optional safe reason. |
| `request_id` | Request correlation ID. |
| `ip_address` | Client IP when available. |
| `user_agent` | Client user agent when available. |
| `metadata` | Safe JSON metadata. |
| `created_at` | Event timestamp. |

## Audit Safety Rules

| Rule | Requirement |
| --- | --- |
| No raw credentials | Never audit raw access tokens, refresh tokens, authorization codes, or device codes. |
| No full secret-bearing bodies | Do not audit complete request bodies that may contain secrets. |
| No raw search queries by default | Store query hash and metadata. |
| Denials audited | Every authorization denial creates an event. |
| Audit transaction | Sensitive operation audit events are written in the same service transaction as the operation. |
| Audit failure behavior | If a required audit event cannot be persisted, the operation fails and rolls back. |
| Audit failures observable | Track audit write failures as a metric and safe log event. |

## Audit Metadata Allowlist

Audit metadata must be small, structured, and safe. Store identifiers and classifications, not raw credential or memory bodies.

| Event group | Allowed metadata examples | Forbidden metadata |
| --- | --- | --- |
| Memory create/update/review/lifecycle | `visibility_scope`, `status_before`, `status_after`, `project_id`, `memory_type`, `field_names_changed`, `reason_code` | Full `body`, full `rationale`, raw source payload, secret-bearing metadata. |
| Grant changes | `grant_id`, `grantee_user_id`, `grant_role` | Full request body beyond allowlisted fields. |
| Authorization denied | `endpoint`, `method`, `resource_type`, `resource_id` when safe, `reason_code` | Secret values, raw body, cross-tenant existence details. |
| Search | `query_hash`, `project_id`, `types`, `statuses`, `tag_count`, `result_count` | Raw query text by default. |
| Context pack | `query_hash`, `task_hash`, `project_id`, `max_items`, `result_count`, `warning_count` | Raw task text by default, generated summaries. |
| Auth/session | `client_type`, `client_name`, `provider`, `session_id`, `reason_code` | Access tokens, refresh tokens, auth codes, device codes, user codes. |
| Admin mutations | `target_user_id`, `group_id`, `project_id`, `role_before`, `role_after`, `is_org_admin_before`, `is_org_admin_after` | Full user profile payloads or secrets. |

Stable denial reason codes:

| Reason code | Meaning |
| --- | --- |
| `missing_capability` | Restricted session lacks required capability. |
| `inactive_user` | User is disabled or not active. |
| `revoked_session` | Session is revoked or expired. |
| `cross_org` | Requested resource belongs to another organization or must be hidden as such. |
| `visibility_audience_miss` | Actor is not in memory visibility audience. |
| `not_reviewer` | Actor cannot review the memory scope. |
| `self_review_denied` | Actor attempted to review own shared memory. |
| `not_owner_or_manager` | Actor lacks owner/manager authority. |
| `session_visibility_cap` | Session maximum visibility scope blocks the request. |

## Logs

Each request log should include:

| Field | Requirement |
| --- | --- |
| Request ID | Correlation ID. |
| Actor user ID | When authenticated. |
| Session ID | When request is authenticated. |
| Org ID | Tenant context. |
| Endpoint | Route/method. |
| Latency | Request duration. |
| Result | Success/error classification. |

Do not log:

| Data | Reason |
| --- | --- |
| Access tokens, refresh tokens, authorization codes, device codes | Credential leakage. |
| Full request bodies | May contain secrets or proprietary memory. |
| Raw search queries | May contain secrets unless policy permits. |

## Technical Metrics

| Metric | Purpose |
| --- | --- |
| Request latency by endpoint | API health. |
| Error rate | Reliability. |
| DB query duration | Database performance. |
| Search latency | Search performance. |
| Context pack latency | Context pack performance. |
| Audit write failures | Audit reliability. |
| Auth/session failures | Security monitoring. |
| Authorization denied count | Permission/security monitoring. |
| Refresh token reuse count | Credential compromise detection. |

## Product Metrics

| Metric | Meaning |
| --- | --- |
| Memories created per week | Adoption. |
| Approval rate | Proposal quality. |
| Review latency | Governance friction. |
| Search success proxy | Search usefulness. |
| Context packs generated | Handover/task usage. |
| Deprecated ratio | Memory health. |
| Needs review ratio | Freshness. |
| Repeated failed attempts avoided | Qualitative value. |

## Embedding Risk Controls For Future

If embeddings are added later:

| Rule | Requirement |
| --- | --- |
| Authorized environment | Do not generate embeddings for content that cannot leave an authorized environment. |
| Secure storage | Do not store embeddings in less secure infrastructure than PostgreSQL. |
| No direct access | Do not allow direct vector store access. |
| Revalidation | Revalidate vector results against PostgreSQL authorization. |
| Visibility sync | Update derived indexes when visibility changes. |
