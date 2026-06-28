# ADR-0005: Separate Context From Visibility

Status: Accepted
Date: 2026-06-28

## Context

A memory can talk about a project without being safe or intended for everyone with project access. If `project_id` implied project visibility, private notes, preliminary ideas, or sensitive observations could leak to a project audience.

## Decision

Separate thematic context from visibility.

`project_id` means the memory is about a project. `visibility_scope` defines who can read it.

Examples:

| `project_id` | `visibility_scope` | Meaning |
| --- | --- | --- |
| `CECW` | `private` | Talks about CECW, only owner reads it. |
| `CECW` | `project` | Talks about CECW and project audience reads it. |
| `CECW` | `group` | Talks about CECW and only selected group reads it. |

## Consequences

Authorization is safer and more explicit. Search and context packs must not treat project association as project visibility. UI filters by project must still use readable memory logic.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| `project_id` implies project visibility | Leaks private project-related memory. |
| Repository-based visibility | Repositories are out of scope. |
| Generic ACL for every context | Too complex for the product. |

## Links

| Spec | File |
| --- | --- |
| Domain model | `specs/domain/model.md` |
| Authorization | `specs/security/authorization.md` |
| Read feature | `specs/features/memory_read_authorization.feature` |
