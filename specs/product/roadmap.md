# Roadmap Spec

## Phase 0: Technical Bootstrap

Estimated duration: 3-5 days.

| Deliverable | Requirement |
| --- | --- |
| Repository initial setup | Python/FastAPI project structure. |
| FastAPI running | Basic app boots. |
| Docker Compose | PostgreSQL available locally. |
| Alembic | Migrations configured. |
| Healthcheck | Basic health endpoint. |
| Configuration | Environment-based settings. |
| README | Developer setup docs. |
| Code quality config | `pyproject.toml`, `pyrightconfig.json`, Ruff, basedpyright, pytest, coverage. |
| CI | Format, lint, type, test, and coverage gates. |

## Phase 1: Core Identity And Permissions

Estimated duration: 1 week.

| Deliverable | Requirement |
| --- | --- |
| Organizations | Data model and service. |
| Users | Data model and service. |
| Org memberships | Roles and membership records. |
| Groups | Groups and hierarchy field. |
| Group memberships | Member/lead roles. |
| Projects | Owning group required. |
| Project memberships | Explicit roles. |
| Effective project roles | Highest role resolution. |
| OIDC auth sessions | Google OIDC first, generic IdP-ready adapter, short-lived access tokens, refresh rotation. |
| ActorContext | Request identity model. |
| AuthorizationService | Core policies and readable query. |
| Admin API | Users, org memberships, groups, group memberships, projects, and project memberships. |
| Tests | Base permission tests. |

## Phase 2: Memory Entries And Review

Estimated duration: 1-2 weeks.

| Deliverable | Requirement |
| --- | --- |
| Create memory | Single create endpoint. |
| Bulk create | Independent entries, no batch entity. |
| Read memory | Authorized detail endpoint. |
| Edit memory | Policy-aware patch endpoint. |
| Evidence | Evidence rows. |
| Restricted grants | Grant add/remove. |
| Review | Approve/reject. |
| Visibility changes | Audience expansion rules. |
| States | Lifecycle status transitions. |
| Audit events | Sensitive events emitted. |

## Phase 3: Search And Context Packs

Estimated duration: 1 week.

| Deliverable | Requirement |
| --- | --- |
| PostgreSQL FTS | `search_vector` and indexes. |
| Search endpoint | Authorized lexical search. |
| Context pack endpoint | Authorized grouped memory packs. |
| Timeline | Basic project timeline. |
| Tests | Search and context pack permission tests. |

## Phase 4: Minimal CLI

Estimated duration: 1 week.

| Deliverable | Requirement |
| --- | --- |
| Login | `nexus login` browser SSO and short-lived session credential storage. |
| Create memory | CLI create command. |
| Bulk upload | CLI bulk command. |
| Search | CLI search. |
| Context pack | CLI context pack command. |
| AI examples | Examples for Codex/OpenCode. |

## Phase 5: Minimal UI

Estimated duration: 1-2 weeks.

| View | Requirement |
| --- | --- |
| Project Memory | Filter by type, status, tag, date, source tool, owner, visibility. |
| Review Queue | Show pending items with approve/reject/edit/mark-needs-review actions. |
| Memory Detail | Show content, status, visibility, project, owner, evidence, source context, audit timeline. |
| Search | Simple authorized memory search. |
| Context Pack View | Generate and display grouped context pack. |

## Future Extensions

| Extension | Notes |
| --- | --- |
| Semantic search | Add EmbeddingProvider, async worker, pgvector/Qdrant behind API, hybrid search, permission revalidation. |
| External integrations | GitHub, PR comments, issues, Telegram public chats, Slack/Teams, meeting transcripts, docs, tickets. |
| Service accounts | Introduce service accounts for integrations without direct human actor. |
| Versioning | Add `memory_entry_revisions` only if legal history, rollback, diff, or exact content audit is needed. |
| Sessions | Add optional `source_sessions` or metadata only if needed, never required for memory creation. |
| Repositories | Add normalized `repositories` only if strong normalization is needed; keep `source_context`. |

## Risk Mitigations

| Risk | Mitigation |
| --- | --- |
| Too much useless information | Structured types, review, ranking, deprecation/archive, product metrics. |
| Incorrect information | Pending review, evidence, confidence as non-binding, human review, needs_review. |
| Information leaks | Private default, project/visibility separation, permission tests, readable query, no direct vector DB, audit. |
| Premature complexity | No sessions, no agents, no repositories, no batches, no versioning, no mandatory vector DB, no LLM in API. |
| Obsolete memory | `review_after`, `needs_review`, `deprecated`, warnings, freshness metrics. |
| Low adoption | Simple CLI, bulk endpoint, no required session, memory templates, fast review queue, handover value. |
