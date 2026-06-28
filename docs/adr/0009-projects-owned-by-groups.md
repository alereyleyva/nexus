# ADR-0009: Projects Are Owned By Groups

Status: Accepted
Date: 2026-06-28

## Context

Projects need clear ownership for access inheritance and governance. Without an owner, projects become orphaned and review responsibility is unclear.

## Decision

Every project must have one required `owning_group_id`.

Members of the owning group derive effective project roles:

| Owning group role | Effective project role |
| --- | --- |
| `member` | `contributor` |
| `lead` | `maintainer` |

Explicit project memberships can add collaborators or higher roles. If multiple roles apply, the highest role wins.

## Consequences

Project ownership is clear. Group leads can act as effective maintainers for owned projects. Collaborators outside the owning group can still be added explicitly.

If ownership is unclear, use a generic group such as Platform, Internal, or Unassigned rather than allowing null ownership.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| Projects without owner | Creates orphaned projects and unclear governance. |
| Many owning groups per project | More complex than product needs. |
| Parent group inheritance | Not designed for product permissions. |

## Links

| Spec | File |
| --- | --- |
| Domain model | `specs/domain/model.md` |
| Authorization | `specs/security/authorization.md` |
| Effective roles feature | `specs/features/effective_project_roles.feature` |
