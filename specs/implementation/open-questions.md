# Open Questions

The original brief is strong on memory, authorization, search, context packs, audit, and architecture. The items below are intentionally listed as unresolved so implementers do not invent hidden product decisions.

## Open Contract Gaps

| ID | Question | Why it matters | Current guidance |
| --- | --- | --- | --- |
| OQ-001 | What are the exact admin endpoints for organizations, users, groups, projects, and memberships? | The data model requires these entities, but the REST endpoint list focuses on memory/search/context/timeline. | Implement minimal internal seed/admin tooling only if needed, or define admin API before building UI flows. |
| OQ-002 | How are user JWTs issued and validated? | The brief requires JWT auth but does not define issuer, claims, or login flow. | Treat JWT verification as an adapter boundary; do not build full SSO unless specified. |
| OQ-003 | What is the API endpoint for creating/revoking personal API tokens? | Token audit events are specified, but endpoint contracts are not. | Define token management endpoints before implementing CLI onboarding. |
| OQ-004 | What is the pagination format for list/search/timeline endpoints? | Search and timeline can grow large. | Use a simple `limit` first; add cursor contract only after specification. |
| OQ-005 | What status codes and error envelope should the API use? | Clients need stable error handling. | Define one error envelope before implementation. |
| OQ-006 | Should review queue have a dedicated endpoint? | UI needs pending review lists, but the endpoint is not listed. | Add a review endpoint spec before building UI Review Queue. |
| OQ-007 | What exact rules apply to editing active shared memory by owners without approval rights? | The brief recommends behavior but leaves room for policy choice. | Prefer moving to `pending_review` when edit expands or materially changes shared active memory without approval rights. |
| OQ-008 | What endpoint archives or soft-deletes memory? | The service responsibilities mention archive/soft delete, but endpoint contracts are absent. | Define explicit archive/delete endpoint before implementing external clients. |
| OQ-009 | Is `org_admin` allowed to configure projects and memberships without knowledge approval powers? | The brief separates `org_admin` from `knowledge_admin`, but admin API details are open. | Keep read access to private memory denied; define admin mutation permissions separately. |
| OQ-010 | Should `confidence` have validation range 0..1? | The DB type implies numeric precision but not a check. | Add check `confidence is null or confidence between 0 and 1` if implementation wants stricter safety. |
| OQ-011 | Should `source_tool` be free text or controlled enum? | Examples include Codex/OpenCode/Cursor/ChatGPT, but future tools are expected. | Keep free text; normalize later only if needed. |
| OQ-012 | Should raw search query auditing ever be enabled? | Queries may contain secrets. | Default to query hash only. Raw query logging requires explicit policy. |
| OQ-013 | Which language config should PostgreSQL FTS use? | Content may be Spanish and English. | Use `simple` as specified; revisit after real corpus analysis. |
| OQ-014 | How should API clients render context packs as Markdown? | The API returns structured JSON and does not call LLMs. | Markdown rendering belongs in CLI/UI clients, not API. |
| OQ-015 | Should there be an explicit healthcheck endpoint? | Roadmap requires healthcheck but API contract does not list it. | Add `GET /health` or similar in bootstrap spec before implementation. |

## Decision Rule

If implementation requires one of these questions, first update the relevant spec and add an ADR when the decision has architectural, security, or long-term maintenance impact.
