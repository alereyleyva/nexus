# Testing Spec

## Testing Principle

Authorization and visibility are product-critical. Tests must be behavior-first and prove that every read path returns only memory the actor is allowed to read.

## Mandatory Test Areas

| Area | Required from day one |
| --- | --- |
| Auth tokens | Token validity, scopes, expiration, revocation, max visibility. |
| Effective project roles | Inherited and explicit role resolution. |
| Memory permissions | Read behavior by visibility and status. |
| Memory creation/review | Initial status and approval rules. |
| Search permissions | Search cannot leak memory. |
| Context pack permissions | Context packs cannot leak memory. |
| Audit | Sensitive operations and denials create audit events. |

## Required Test Files

| File | Purpose |
| --- | --- |
| `tests/test_auth_tokens.py` | Token auth and scope behavior. |
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
| Org admin boundary | `org_admin` cannot read private memory owned by another user. |
| Private visibility | Private memory is readable only by owner. |
| Restricted visibility | Restricted memory is readable by owner and explicit grantees only. |
| Group visibility | Group memory is readable only by group members. |
| Project visibility | Project memory is readable only by users with effective project access. |
| Organization visibility | Organization memory is readable only by active org members. |
| Token restriction | CLI token cannot exceed user permissions. |
| Pending hidden | `pending_review` is hidden from normal search/context packs. |
| Rejected hidden | `rejected` is hidden from normal search/context packs. |
| Deprecated explicit | `deprecated` appears only when explicitly requested and authorized. |
| Search safety | Search never returns something detail GET would deny. |
| Context pack safety | Context packs never return something search would not return. |
| Denial audit | Every authorization denial emits audit event. |

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

## Gherkin Mapping

The `specs/features/*.feature` files are the acceptance-test source. Automated tests should map scenario names to test names or comments.
