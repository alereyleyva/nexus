# ADR-0002: Memory Entries, Not Mandatory Sessions

Status: Accepted
Date: 2026-06-28

## Context

AI sessions can be long, incomplete, interrupted, or mixed across tasks. Requiring `create_session`, `append_message`, and `close_session` would add friction and integrity problems. The product goal is to capture reusable knowledge, not complete conversations.

## Decision

Use independent memory entries as the primary unit of the system.

Clients submit structured memory directly through:

```http
POST /v1/memory-entries
```

If multiple entries come from the same thread/chat, they may share `source_ref`, but they do not depend on a formal session resource.

## Consequences

Memory capture is simpler for CLIs/plugins. Entries can be created whenever useful knowledge appears. Bulk upload creates independent entries and must not create a capture batch entity.

Future sessions may be added as optional metadata or a `source_sessions` entity, but never as a requirement for memory creation.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| Mandatory session model | High client friction and ambiguous lifecycle. |
| Message transcript storage | Product explicitly avoids storing full conversations. |
| Capture batches | Adds resource complexity without product need. |

## Links

| Spec | File |
| --- | --- |
| Product non-goals | `specs/product/overview.md` |
| API bulk behavior | `specs/api/rest-api.md` |
| API feature | `specs/features/api_contracts.feature` |
