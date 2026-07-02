# ADR-0003: Users, Not AI Tools, Are Permission Actors

Status: Accepted
Date: 2026-06-28

## Context

Developers use tools such as Codex, OpenCode, Cursor, and ChatGPT. Those tools may propose memory, but the organization must govern memory through human accountability and user permissions.

Introducing AI agents or tools as permission principals in the product would complicate authorization and audit before there is a concrete need.

## Decision

Real users are the only permission actors in the product. AI tools are recorded as source metadata, not as actors.

Example audit semantics:

```text
Morgan created this memory using Codex CLI.
```

Not:

```text
Codex created this memory.
```

Short-lived Nexus session credentials act on behalf of users and may restrict user permissions. They never create a non-human permission actor.

## Consequences

Audit remains human-accountable. Authorization stays simpler. Tool-specific behavior is represented through `source_kind`, `source_tool`, `source_ref`, and `submitted_via_session_id`.

Future service accounts may be introduced for integrations without a human actor, but agents should not become permission principals until a clear case exists.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| AI agents as principals | Premature IAM complexity. |
| Source tools as actors | Weak human accountability. |
| `X-On-Behalf-Of` for product | Not needed because session credentials belong to a user. |

## Links

| Spec | File |
| --- | --- |
| Authorization | `specs/security/authorization.md` |
| Auth feature | `specs/features/auth_and_sessions.feature` |
| API contracts | `specs/features/api_contracts.feature` |
