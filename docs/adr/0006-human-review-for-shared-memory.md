# ADR-0006: Human Review For Shared Memory

Status: Accepted
Date: 2026-06-28

## Context

AI-assisted work can produce useful but incorrect or speculative knowledge. Private notes can be active immediately because the owner controls their own memory. Shared memory affects groups, projects, or the whole organization and needs governance.

## Decision

Use status and role-based review for shared memory.

Initial status depends on visibility and actor authority:

| Scope | Non-approver result | Approver result |
| --- | --- | --- |
| `private` | `active` | `active` |
| `restricted` | `active` | `active` |
| `group` | `pending_review` for group member | `active` for group lead |
| `project` | `pending_review` for contributor | `active` for reviewer/maintainer |
| `organization` | `pending_review` for member | `active` for knowledge admin |

## Consequences

Shared knowledge is safer and more trustworthy. Review queues become part of the product. Search and context packs exclude pending and rejected memory by default.

Contributors can still propose knowledge without being blocked, but their shared proposals require approval.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| All shared memory active immediately | Too much risk of incorrect organizational memory. |
| All memory requires review | Too much friction for private/restricted use. |
| Confidence score as approval | Confidence is not a governance substitute. |

## Links

| Spec | File |
| --- | --- |
| Authorization | `specs/security/authorization.md` |
| Testing | `standards/testing.md` |
| Creation feature | `specs/features/memory_creation_and_review.feature` |
