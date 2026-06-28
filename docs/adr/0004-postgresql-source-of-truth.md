# ADR-0004: PostgreSQL Is The Source Of Truth

Status: Accepted
Date: 2026-06-28

## Context

Nexus stores governed organizational knowledge with strict authorization, review state, evidence, grants, tokens, and audit. Future semantic search may require vector indexes, but vector stores should not become canonical data stores.

## Decision

Use PostgreSQL as the source of truth for organizations, users, groups, projects, memory entries, evidence, grants, tokens, and audit events.

Future vector stores or search indexes are derived indexes only. They must remain behind the API and must revalidate results against PostgreSQL authorization rules.

## Consequences

Data consistency, auditability, and permissions remain centralized. PostgreSQL can enforce tenant isolation through `org_id`, composite foreign keys, constraints, and transactions.

Future semantic search must handle index synchronization when memory content, status, or visibility changes.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| Qdrant as direct access path | Would bypass API authorization and audit. |
| Vector store as source of truth | Poor fit for relational permissions and governance. |
| Multiple canonical stores | Increases consistency risk. |

## Links

| Spec | File |
| --- | --- |
| Data model | `specs/data/schema.dbml` |
| Search | `specs/search/search-and-context-packs.md` |
| Security | `specs/security/security-observability-audit.md` |
