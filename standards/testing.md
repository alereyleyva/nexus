# Testing Spec

## Testing Principle

Authorization and visibility are product-critical. Tests must be behavior-first and prove that every read path returns only memory the actor is allowed to read.

## Mandatory Test Areas

| Area | Required from day one |
| --- | --- |
| Auth sessions | OIDC session validity, refresh rotation, expiration, revocation, capabilities, max visibility. |
| Error contract | Common problem envelope and stable error codes. |
| Pagination | Cursor pagination consistency and authorization-safe page boundaries. |
| Admin API | Org admin boundaries and membership/project/group mutations. |
| Effective project roles | Inherited and explicit role resolution. |
| Memory permissions | Read behavior by visibility and status. |
| Memory creation/review | Initial status and approval rules. |
| Search permissions | Search cannot leak memory. |
| Context pack permissions | Context packs cannot leak memory. |
| Audit | Sensitive operations and denials create audit events. |

## Required Test Files

| File | Purpose |
| --- | --- |
| `tests/test_auth_sessions.py` | OIDC session auth, refresh rotation, and session restriction behavior. |
| `tests/test_error_contract.py` | Problem Details envelope and stable status/code mapping. |
| `tests/test_pagination.py` | Cursor behavior for list/search/timeline/review queue. |
| `tests/test_admin_api.py` | Admin API permissions and org admin boundaries. |
| `tests/test_project_effective_roles.py` | Effective project role derivation. |
| `tests/test_memory_permissions.py` | Visibility/status read rules. |
| `tests/test_memory_creation_review.py` | Creation, review, status transitions. |
| `tests/test_search_permissions.py` | Search safety. |
| `tests/test_context_pack_permissions.py` | Context pack safety. |
| `tests/test_audit.py` | Audit emission and metadata safety. |

## Security Invariants

| Invariant | Required proof |
| --- | --- |
| Cross-org isolation | A user cannot read memory from another organization. |
| Org admin boundary | `is_org_admin = true` cannot read private memory owned by another user. |
| Private visibility | Private memory is readable only by owner. |
| Restricted visibility | Restricted memory is readable by owner and explicit grantees only. |
| Group visibility | Group memory is readable only by group members. |
| Project visibility | Project memory is readable only by users with effective project access. |
| Organization visibility | Organization memory is readable only by active org members. |
| Session restriction | CLI session cannot exceed user permissions. |
| Session revocation | Revoked sessions cannot authenticate or refresh. |
| Refresh rotation | Reusing an old refresh token revokes the session. |
| Pending hidden | `pending_review` is hidden from normal search/context packs. |
| Rejected hidden | `rejected` is hidden from normal search/context packs. |
| Deprecated explicit | `deprecated` appears only when explicitly requested and authorized. |
| Search safety | Search never returns something detail GET would deny. |
| Context pack safety | Context packs never return something search would not return. |
| Denial audit | Every authorization denial emits audit event. |
| Error envelope | Every non-2xx API response uses the common problem envelope. |
| Admin boundary | `is_org_admin = true` can configure org structure but cannot read private memory or approve organization memory unless `role = knowledge_admin`. |
| Self-review denied | Owners/creators cannot approve, reject, or reconfirm their own shared memory. |
| Bulk atomicity | Bulk create fails the whole request when any entry is invalid or unauthorized. |

## Effective Role Tests

| Case | Expected result |
| --- | --- |
| Group member of owning group | Effective project role `contributor`. |
| Group lead of owning group | Effective project role `maintainer`. |
| Explicit viewer | Can read but cannot create/propose. |
| Explicit reviewer | Can approve project memory. |
| Multiple access paths | Highest role wins. |

## Creation And Review Tests

| Case | Expected result |
| --- | --- |
| Active user creates private memory | Status `active`. |
| Active user creates restricted memory | Status `active`. |
| Group member creates group memory | Status `pending_review`. |
| Group lead creates group memory | Status `active`. |
| Project contributor creates project memory | Status `pending_review`. |
| Project reviewer creates project memory | Status `active`. |
| Project maintainer creates project memory | Status `active`. |
| Org member creates organization memory | Status `pending_review`. |
| Knowledge admin creates organization memory | Status `active`. |
| Reviewer approves project memory | Status becomes `active`. |
| Unauthorized contributor approves project memory | Denied and audited. |
| Knowledge admin approves organization memory | Status becomes `active`. |
| Creator tries to approve own shared memory | Denied and audited. |

## Auth Session Tests

| Case | Expected result |
| --- | --- |
| Google OIDC login creates session | Actor context resolves active user and org. |
| CLI login exchange | Authorized CLI device code returns access token, refresh token, and session id. |
| CLI token polling before approval | Returns `authorization_pending`. |
| Reused CLI device code | Returns conflict and does not create another session. |
| Disabled user uses existing access token | Request denied and audited. |
| Revoked session uses access token | Request denied and audited. |
| Refresh token rotation | New refresh token is returned and old token becomes used. |
| Refresh token reuse | Session is revoked and `auth.refresh_reuse_detected` is emitted. |
| Session missing capability | Restricted session cannot call endpoint requiring absent capability. |
| Session max visibility | CLI session cannot create or expand memory above max visibility. |

## Admin API Tests

| Case | Expected result |
| --- | --- |
| `is_org_admin = true` creates group | Group created and admin audit event emitted. |
| `is_org_admin = true` assigns project membership | Membership updated and effective role changes. |
| Non org admin calls admin endpoint | Denied and audited. |
| `is_org_admin = true` reads another user's private memory | Denied by normal memory authorization. |
| `is_org_admin = true` alone approves organization memory | Denied unless `role = knowledge_admin`. |
| Last org admin removal | Denied. |

## Error And Pagination Tests

| Case | Expected result |
| --- | --- |
| Validation failure | Returns `422` with `VALIDATION_FAILED` problem envelope. |
| Missing auth | Returns `401` with `UNAUTHENTICATED` problem envelope. |
| Unauthorized hidden resource read | Returns `404` or configured denial status and emits denial audit. |
| Invalid cursor | Returns `400` with `BAD_REQUEST`. |
| Paginated search | Uses stable cursor and never returns unauthorized memory on later pages. |
| Review queue pagination | Returns only reviewable memory across page boundaries. |

## Search Tests

| Case | Expected result |
| --- | --- |
| Search by title | Matching authorized entries returned. |
| Search by body | Matching authorized entries returned. |
| Search by rationale | Matching authorized entries returned. |
| Search by tags | Matching authorized entries returned. |
| Filter by project | Only matching project-associated authorized memory returned. |
| Filter by type | Only selected types returned. |
| Filter by status | Only allowed selected statuses returned. |
| Unauthorized memory exists | It is not returned. |
| Pending/rejected default | They are not returned. |

## Context Pack Tests

| Case | Expected result |
| --- | --- |
| Group by type | Items are grouped into type buckets. |
| Respect permissions | Unauthorized memory absent. |
| Exclude deprecated default | Deprecated memory absent by default. |
| Needs review warnings | Warnings included for `needs_review` items. |
| Respect max items | Total items do not exceed request limit. |
| Respect project ID | Project filter applied without visibility bypass. |

## Audit Tests

| Case | Expected result |
| --- | --- |
| Create memory | `memory_entry.created` emitted. |
| Approve memory | `memory_entry.approved` emitted. |
| Reject memory | `memory_entry.rejected` emitted. |
| Change visibility | `memory_entry.visibility_changed` emitted. |
| Add grant | `memory_entry.grant_added` emitted. |
| Remove grant | `memory_entry.grant_removed` emitted. |
| Search | `search.executed` emitted without raw query by default. |
| Context pack | `context_pack.generated` emitted. |
| Authorization denied | `authorization.denied` emitted. |
| Session created | `auth.session.created` emitted. |
| Session revoked | `auth.session.revoked` emitted. |
| Soft delete memory | `memory_entry.deleted` emitted. |

## Gherkin Mapping

The `specs/features/*.feature` files are the acceptance-test source. Automated tests should map scenario names to test names or comments.
