# ADR-0008: No LLM Or Embeddings In API

Status: Accepted
Date: 2026-06-28

## Context

AI tools help users create memory proposals during their work sessions. The API should validate, persist, review, search, audit, and serve memory. Calling LLMs from the API would add latency, cost, security review, provider configuration, and unpredictable behavior before core governance is validated.

## Decision

The API must not call LLMs and must not generate embeddings.

AI behavior belongs outside the API, in the developer's AI tool, CLI, plugin, or UI client. Context packs return structured JSON only; clients may transform that JSON into natural-language context locally.

## Consequences

The API is deterministic, easier to test, and easier to secure. The product can validate governed memory without AI-provider dependency.

Future LLM or embedding features require new specs and ADRs.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| API summarizes context packs with LLM | Violates product boundary and adds provider risk. |
| API generates embeddings at create time | Embeddings are out of scope. |
| Semantic search from day one | Premature complexity. |

## Links

| Spec | File |
| --- | --- |
| Product non-goals | `specs/product/overview.md` |
| Context packs | `specs/search/search-and-context-packs.md` |
| Context feature | `specs/features/context_packs.feature` |
