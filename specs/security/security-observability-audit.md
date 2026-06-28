# Security, Observability, And Audit Spec

## Security Baseline

| Rule | Requirement |
| --- | --- |
| TLS | Use TLS in transit. |
| Encryption at rest | Use PostgreSQL/storage encryption if infrastructure offers it. |
| Secret management | Keep secrets out of the repository. |
| Token storage | Store token hashes only, never raw tokens. |
| Soft delete | Use soft delete for memory entries. |
| Sensitive changes | Audit visibility, review, grants, denial, token lifecycle, search, and context pack generation. |
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
| `search.executed` | Search executed. |
| `context_pack.generated` | Context pack generated. |
| `authorization.denied` | Access denied. |
| `token.created` | Token created. |
| `token.revoked` | Token revoked. |

## Audit Event Data

Each audit event includes:

| Field | Requirement |
| --- | --- |
| `org_id` | Required organization. |
| `actor_user_id` | Acting user if known. |
| `actor_token_id` | Token if request used a personal API token. |
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
| No raw tokens | Never audit raw tokens. |
| No full secret-bearing bodies | Do not audit complete request bodies that may contain secrets. |
| No raw search queries by default | Store query hash and metadata. |
| Denials audited | Every authorization denial creates an event. |
| Audit failures observable | Track audit write failures as a metric. |

## Logs

Each request log should include:

| Field | Requirement |
| --- | --- |
| Request ID | Correlation ID. |
| Actor user ID | When authenticated. |
| Token ID | When API token is used. |
| Org ID | Tenant context. |
| Endpoint | Route/method. |
| Latency | Request duration. |
| Result | Success/error classification. |

Do not log:

| Data | Reason |
| --- | --- |
| Tokens | Credential leakage. |
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
| Token authentication failures | Security monitoring. |
| Authorization denied count | Permission/security monitoring. |

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
