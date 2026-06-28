# ADR-0007: PostgreSQL Full Text Search First

Status: Accepted
Date: 2026-06-28

## Context

The product must support useful search while keeping permissions correct. Semantic search and vector stores add operational complexity and permission risks. Nexus needs to validate core value before adding embeddings.

## Decision

Use PostgreSQL Full Text Search in the product.

`search_vector` is built from title, body, rationale, tags, and optionally relevant source context parts. Use `simple` text search configuration initially for mixed Spanish/English content.

Search must start from readable memory entries and then apply full text search.

## Consequences

The product has lower complexity and fewer dependencies. Authorization is easier to enforce. Ranking can combine text rank, freshness, type priority, and status score.

Future semantic search can be added behind the API with permission revalidation.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| Embeddings in product | Unnecessary complexity and security review. |
| Qdrant/Pinecone/Weaviate in product | Additional infrastructure and permission risk. |
| Search all then filter in memory | Risky and explicitly forbidden. |

## Links

| Spec | File |
| --- | --- |
| Search | `specs/search/search-and-context-packs.md` |
| Search feature | `specs/features/search.feature` |
| Security | `specs/security/security-observability-audit.md` |
