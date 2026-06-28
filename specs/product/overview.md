# Product Spec

## Product

| Field | Value |
| --- | --- |
| Name | Nexus |
| Type | Governed shared memory API for AI-assisted teams |
| Spec date | 2026-06-28 |
| Primary users | Developers, tech leads, reviewers, knowledge admins, AI-assisted workflows |
| Primary clients | CLI, AI tool plugin, UI, future integrations |

## One Sentence Idea

Each time a person works with AI on a project, the organization can learn something reusable; Nexus turns that learning into structured, secure, reviewable, searchable memory.

## Problem

Important company knowledge often lives outside formal documentation: conversations, meetings, chats, emails, PRs, tickets, informal decisions, and AI tool sessions. AI-assisted work produces useful knowledge, but that knowledge is commonly trapped in a private chat, local terminal, or tool-specific memory.

## Typical Failure Cases

| Case | Impact |
| --- | --- |
| A developer solves a complex bug with AI but does not record the root cause. | Future debugging repeats the same work. |
| A solution is tried and discarded but not captured. | Another developer repeats the failed attempt. |
| A technical decision loses its rationale. | Future changes lack context. |
| A person goes on vacation or changes team. | Handover depends on fragile human recall. |
| A new member joins a project. | They rebuild months of history manually. |
| An AI agent starts a task without prior decisions, risks, or procedures. | It proposes unsafe or duplicated work. |

## Product Goals

| Goal | Requirement |
| --- | --- |
| Store organizational memory | Persist structured knowledge entries. |
| Project association | Allow entries to optionally reference a project. |
| Context/visibility separation | Referencing a project must not imply project visibility. |
| Governance | Control read, create, review, approve, archive, and share operations. |
| AI tool compatibility | Allow CLI/plugin tools to submit memory on behalf of users. |
| No API-side AI | Do not call LLMs from the API in the product. |
| Safe search | Return only authorized memory. |
| Context packs | Generate structured packs for humans or AI tools. |
| Auditability | Record relevant operations and denials. |
| Extensibility | Prepare for semantic search, integrations, and multi-agent use later. |

## Business Goals

| Goal | Value |
| --- | --- |
| Handover | Faster continuity between people. |
| Onboarding | Better context for new developers. |
| Knowledge reuse | Fewer repeated decisions and fixes. |
| Silo reduction | Knowledge moves from individual sessions to governed shared memory. |
| Duplicate work reduction | Failed attempts and known procedures are discoverable. |
| AI context | AI tools can start tasks with authorized prior memory. |
| Governance | Shared knowledge is reviewed and traceable. |

## Technical Goals

| Goal | Requirement |
| --- | --- |
| Simple | Avoid premature complexity. |
| Secure by design | Default private, explicit visibility, no bypass reads. |
| Auditable | Sensitive operations create audit events. |
| Multi-tenant | Organization isolation through `org_id`. |
| API-first | All access passes through the API. |
| Testable | Permission and state invariants are automated from day one. |
| CLI/plugin ready | `nexus login` creates short-lived session credentials that act on behalf of users. |
| PostgreSQL-first | No vector store as source of truth. |

## Product Non-Goals

| Non-goal | Decision |
| --- | --- |
| Mandatory source sessions | Do not model AI chats, terminal sessions, or source sessions as required memory resources. Auth sessions are separate login infrastructure. |
| AI agents as permission principals | AI tools are source tools, not permission actors. |
| Repositories as core entities | Store repo, branch, commit, PR, and files in `source_context`. |
| Capture batches | Bulk upload creates independent entries, not batches. |
| Entry versioning | Use operational audit, not full content revision history. |
| LLM inside API | The API does not call models in the product. |
| Embeddings | Do not generate embeddings in the product. |
| Direct Qdrant/vector access | Future vector stores stay behind the API. |
| Telegram/GitHub/Slack ingestion | Future integration work, not product core. |
| MCP server | Future, after API core. |
| Generic IAM/ACL engine | Use a simple strong visibility model. |

## Product User Workflows

| Workflow | Expected behavior |
| --- | --- |
| Save private memory | User submits a private entry and it becomes `active`. |
| Propose project memory | Contributor submits project memory and it becomes `pending_review`. |
| Create official project memory | Reviewer/maintainer submits project memory and it becomes `active`. |
| Review memory | Authorized reviewer approves or rejects `pending_review` memory. |
| Handover | User requests a context pack and receives grouped authorized memory. |
| Restricted sharing | Owner shares restricted memory with explicit grants. |
| Search | User searches only memory they could read directly. |

## Product Acceptance Criteria

| Criterion | Acceptance |
| --- | --- |
| Private memory | A user can create private memory. |
| Project memory | A user can propose project memory. |
| Project review | A reviewer can approve project memory. |
| Authorized search | A user can search authorized memory. |
| Search safety | Search never returns unauthorized memory. |
| Context pack safety | Context packs never return unauthorized memory. |
| Project association safety | A memory can reference a project without becoming project-visible. |
| Owning group access | A project inherits access from its owning group. |
| External project user | A user outside the project does not see project memory. |
| Org admin boundary | An org admin does not automatically read others' private memory. |
| Restricted grants | Explicit grants allow restricted sharing. |
| Audit | Sensitive operations are audited. |
| No LLM | The API does not call an LLM. |
| PostgreSQL source of truth | PostgreSQL stores canonical data. |
| Automated tests | Permission tests exist from day one. |

## Product Phrase

Nexus converts daily AI-assisted work into secure, reviewable, reusable organizational memory.
