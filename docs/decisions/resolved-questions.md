# Resolved Decisions

The original brief left several implementation questions open so implementers would not invent hidden product behavior. The questions below are now resolved and linked to the canonical specs that define the behavior.

There are no known blocking open questions as of 2026-06-28.

| ID | Decision | Canonical spec |
| --- | --- | --- |
| OQ-001 | Provide organization admin APIs for users, org memberships, groups, group memberships, projects, and project memberships. These endpoints back the UI configuration flows. | `../api/rest-api.md`, `../security/authorization.md` |
| OQ-002 | Use OIDC SSO to issue Nexus auth sessions. Google is the first provider; generic OIDC IdP support must fit behind the provider adapter. Nexus issues short-lived access JWTs and rotated opaque refresh tokens. | `../../docs/adr/0010-oidc-short-lived-user-sessions.md`, `../api/rest-api.md`, `../security/authorization.md` |
| OQ-003 | Do not build long-lived static user credentials in v1. CLI uses `nexus login` with browser SSO and short-lived session credentials. | `../../docs/adr/0010-oidc-short-lived-user-sessions.md`, `../product/ui-cli.md` |
| OQ-004 | Use keyset cursor pagination for list/search/timeline/review/admin endpoints: `limit`, opaque `cursor`, `page.next_cursor`, `page.has_more`, no `total_count` in v1. | `../api/rest-api.md` |
| OQ-005 | Use one scalable API error envelope based on Problem Details with stable `code`, `request_id`, optional `errors`, and documented status-code mapping. | `../../docs/adr/0011-api-error-contract.md`, `../api/rest-api.md` |
| OQ-006 | Add `GET /v1/review-queue` for pending and explicitly requested `needs_review` items that the actor can review. | `../api/rest-api.md` |
| OQ-007 | Active approved shared memory stays `active` when edited by an actor with control over that memory. Non-controllers are denied and should create a new proposal instead. | `../security/authorization.md`, `../api/rest-api.md` |
| OQ-008 | Add `POST /v1/memory-entries/{id}/archive` and `DELETE /v1/memory-entries/{id}`. Archive is normal for active shared memory; delete is soft delete for eligible private/restricted memory or pending proposal withdrawal. | `../api/rest-api.md`, `../security/authorization.md` |
| OQ-009 | `is_org_admin = true` can configure organization structure and memberships but does not read private memory or approve organization memory unless also authorized by normal memory rules or `role = knowledge_admin`. | `../security/authorization.md`, `../api/rest-api.md` |
| OQ-010 | `confidence` must be null or between 0 and 1. | `../domain/model.md`, `../data/schema.dbml`, `../api/rest-api.md` |
| OQ-011 | `source_tool` remains free text to support new tools without migrations. | `../domain/model.md` |
| OQ-012 | Raw search query auditing is disabled by default. Store query hash and safe metadata only unless an explicit internal policy later allows raw query logging. | `../search/search-and-context-packs.md`, `../security/security-observability-audit.md` |
| OQ-013 | PostgreSQL FTS uses the `simple` configuration initially because content may mix Spanish and English. | `../search/search-and-context-packs.md` |
| OQ-014 | Context pack Markdown rendering belongs in CLI/UI clients. The API returns structured JSON and does not call LLMs. | `../api/rest-api.md`, `../product/ui-cli.md` |
| OQ-015 | Add unauthenticated healthcheck endpoints: `GET /health`, `GET /health/live`, and `GET /health/ready`. | `../api/rest-api.md`, `../product/roadmap.md` |
| OQ-016 | Product-initial authentication uses Google SSO through OIDC. The CLI uses `nexus login`, opens browser SSO, and exchanges an approved one-time device authorization for short-lived Nexus session credentials. Generic OIDC remains an adapter-compatible future extension, not additional v1 behavior. | `../../docs/adr/0010-oidc-short-lived-user-sessions.md`, `../api/rest-api.md`, `../security/authorization.md` |
| OQ-017 | Public API resource identifiers are canonical UUID strings in v1. Do not introduce prefixed public ids such as `mem_123`, `usr_123`, or `prj_123`; examples should use UUID-shaped values. | `../api/rest-api.md`, `../data/schema.dbml` |
| OQ-018 | Organization knowledge approval and organization administration are separate capabilities. `org_memberships.role` represents knowledge role (`member` or `knowledge_admin`), and `org_memberships.is_org_admin` controls organization configuration endpoints. A user may have neither, either, or both. | `../domain/model.md`, `../data/schema.dbml`, `../security/authorization.md` |
| OQ-019 | Backend implementation uses synchronous FastAPI route functions with synchronous SQLAlchemy 2 `Session`. Do not introduce async SQLAlchemy or mixed sync/async persistence unless a future ADR changes this. | `../../standards/backend/implementation-templates.md`, `../../standards/python/style.md` |
| OQ-020 | Memory detail and mutation endpoints hide inaccessible memory as `404 NOT_FOUND`; operation-level denials on otherwise visible resources return `403 AUTHORIZATION_DENIED`; invalid lifecycle transitions return `409 CONFLICT`. All authorization denials are audited. | `../api/rest-api.md`, `../security/authorization.md` |
| OQ-021 | A memory owner remains in the read audience for their own non-deleted memory across visibility scopes, subject to status/query-mode rules and active-user/session checks. Explicit grants apply only to `restricted` memory. | `../security/authorization.md`, `../domain/model.md` |
| OQ-022 | Self-review is prohibited for shared memory. The user who created or owns a `pending_review` or `needs_review` shared entry cannot approve, reject, or reconfirm it; another authorized reviewer must do so. | `../security/authorization.md`, `../api/rest-api.md` |
| OQ-023 | Bulk memory create is all-or-nothing in v1. Validate all entries first, then create all entries in one transaction; any invalid or unauthorized entry fails the whole request. Per-entry idempotency still applies inside the transaction. | `../api/rest-api.md` |
| OQ-024 | Audit writes for sensitive operations are part of the same service transaction. If the audit event cannot be persisted, the operation fails and rolls back; audit write failures are also observable as metrics/logs without leaking sensitive bodies. | `../security/security-observability-audit.md`, `../../standards/backend/error-audit-patterns.md` |

## Decision Rule

If implementation reveals a new ambiguity, update the relevant spec first and add an ADR when the decision has architectural, security, or long-term maintenance impact.
