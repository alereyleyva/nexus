# Search And Context Packs Spec

## Search

The product uses PostgreSQL Full Text Search. It must not use embeddings, Qdrant, Pinecone, Weaviate, or external semantic search initially.

## Search Rationale

| Reason | Benefit |
| --- | --- |
| Lower complexity | Faster implementation. |
| Easier authorization | Search starts from readable memory query. |
| Fewer dependencies | No vector service required. |
| Traceability | PostgreSQL remains canonical. |
| Lower cost | Simpler operations. |

## Search Vector Fields

`search_vector` should be built from:

| Field | Weight guidance |
| --- | --- |
| `title` | A |
| `body` | B |
| `rationale` | C |
| `tags` | B |
| relevant `source_context` parts | Future/optional enhancement |

Example:

```sql
update memory_entries
set search_vector =
  setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
  setweight(to_tsvector('simple', coalesce(body, '')), 'B') ||
  setweight(to_tsvector('simple', coalesce(rationale, '')), 'C') ||
  setweight(to_tsvector('simple', array_to_string(tags, ' ')), 'B')
where id = :id;
```

Use PostgreSQL `simple` text search configuration for Nexus because content may be mixed Spanish/English.

## Secure Search Rule

Search must start from the actor-readable memory query.

Not allowed:

```text
search everything -> filter in application memory
```

Allowed:

```text
readable_memory_entries(actor) + full text search
```

## Search Filters

| Filter | Behavior |
| --- | --- |
| `query` | Full text query. Empty or omitted query is allowed only when at least one structured filter is present. |
| `project_id` | Restrict to memory associated to project, without bypassing visibility. |
| `types` | Restrict by memory types. |
| `statuses` | Restrict by allowed statuses. Hidden statuses require explicit authorized mode. |
| `tags` | Restrict by tags using AND semantics: every requested tag must be present. |
| `limit` | Limit result count. |
| `cursor` | Continue from a previous search page using the common opaque cursor contract. |
| `include_evidence` | Include evidence details or counts according to response schema. |

Filter combination uses AND semantics across different filter classes.

## Default Search Statuses

| Status | Included by default |
| --- | --- |
| `active` | Yes |
| `needs_review` | Yes, with warning/marker |
| `pending_review` | No |
| `rejected` | No |
| `deprecated` | No, unless explicitly requested and authorized |
| `archived` | No |

## Ranking

Initial score is deterministic:

```text
score = text_rank * 0.75
      + freshness_score * 0.10
      + type_priority * 0.10
      + status_score * 0.05
```

Component rules:

| Component | Rule |
| --- | --- |
| `text_rank` | `ts_rank_cd(search_vector, websearch_to_tsquery('simple', query))`; use `0` when query is empty. |
| `freshness_score` | `1.0` when `updated_at` is within 30 days, `0.5` within 180 days, otherwise `0.0`. |
| `type_priority` | `1.0` high, `0.75` medium-high, `0.5` medium, `0.25` low. |
| `status_score` | `1.0` for `active`, `0.5` for `needs_review`, `0.25` for explicitly requested `deprecated`, `0.0` for explicitly requested `archived`. |
| Ordering | Sort by `score desc, updated_at desc, id desc`. |

## Type Priority For Context

| Type | Priority |
| --- | --- |
| `decision` | High |
| `procedure` | High |
| `risk` | High |
| `problem` | Medium-high |
| `solution` | Medium-high |
| `failed_attempt` | Medium-high |
| `open_question` | Medium |
| `task` | Medium |
| `note` | Low |

## Search Audit

Search must emit `search.executed`. Do not store raw query text by default because it may contain secrets.

Recommended metadata:

```json
{
  "query_hash": "sha256:...",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "result_count": 8,
  "types": ["decision", "problem"]
}
```

Raw query logging is allowed only with an explicit internal policy.

## Context Pack Definition

A context pack is a structured response that groups memory relevant to a task. It is not persisted. It does not call AI, generate memory, or summarize with LLMs.

## Context Pack Behavior

| Rule | Requirement |
| --- | --- |
| Authorization | Use the same read rule as search. |
| No pending review | Exclude `pending_review`. |
| No rejected | Exclude `rejected`. |
| Deprecated default | Exclude `deprecated` unless explicitly configured. |
| Private safety | Include private memory only if actor is owner or has grant via restricted. |
| Grouping | Group by memory type. |
| Limits | Respect `max_items`. |
| Warnings | Include warnings for `needs_review` memory. |
| Audit | Emit `context_pack.generated`. |

Context pack selection starts from search behavior with the same authorization, filters, score, and tie-breakers. It then groups selected items by memory type.

Allocator rules:

| Rule | Requirement |
| --- | --- |
| Type order | Fill groups in this order: `decision`, `procedure`, `risk`, `problem`, `solution`, `failed_attempt`, `open_question`, then optional `task`, `note`. |
| Per-type ordering | Within each group, preserve search ordering. |
| Max items | Stop when total selected items reaches `max_items`. |
| Default `max_items` | `20`. |
| Maximum `max_items` | `50`. |

## Context Pack Group Keys

| Memory type | Response group |
| --- | --- |
| `decision` | `decisions` |
| `problem` | `problems` |
| `solution` | `solutions` |
| `failed_attempt` | `failed_attempts` |
| `risk` | `risks` |
| `procedure` | `procedures` |
| `open_question` | `open_questions` |
| `task` | `tasks` if included by future UI/client. |
| `note` | `notes` if included by future UI/client. |

## AI Tool Usage

A client may call `POST /v1/context-packs` before starting a task. The AI tool may transform the returned JSON into natural language inside its own session. The API must not do that transformation in the API.

## Project Timeline

Project timeline returns project-related events such as memory creation and approval. It must only include memory the actor is authorized to read. It should use audit events and memory metadata as the event source.

Timeline responses use the common cursor pagination contract from `../api/rest-api.md` with ordering `timestamp desc, id desc`.

## Future Semantic Search Rules

When semantic search is added:

| Rule | Requirement |
| --- | --- |
| Derived index only | Vector store is never source of truth. |
| API-only access | No direct vector store access. |
| Permission revalidation | Candidate IDs from vector search are revalidated against PostgreSQL readable query. |
| Visibility updates | Derived indexes update when visibility changes. |
| Security parity | Embeddings must not be stored in less secure infrastructure than PostgreSQL. |

Future flow:

```text
Query
-> vector search returns candidate IDs
-> API revalidates candidate IDs against readable_memory_entries(actor)
-> API returns only authorized results
```
