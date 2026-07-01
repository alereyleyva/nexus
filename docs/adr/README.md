# Architectural Decision Records

ADRs record durable architectural decisions for Nexus. They are binding unless superseded by a newer ADR.

## Index

| ADR | Decision |
| --- | --- |
| `0001-modular-monolith-api-first.md` | Build the product as an API-first modular monolith. |
| `0002-memory-entries-not-sessions.md` | Use independent memory entries as the primary unit. |
| `0003-users-not-ai-tools-are-permission-actors.md` | Use real users as permission actors; AI tools are sources. |
| `0004-postgresql-source-of-truth.md` | Use PostgreSQL as the source of truth. |
| `0005-separate-context-from-visibility.md` | Separate project/source context from visibility. |
| `0006-human-review-for-shared-memory.md` | Require governance/review for shared memory. |
| `0007-postgresql-full-text-search-first.md` | Use PostgreSQL full text search for product search. |
| `0008-no-llm-or-embeddings-in-api.md` | Do not call LLMs or generate embeddings in the API. |
| `0009-projects-owned-by-groups.md` | Require each project to have one owning group. |
| `0010-oidc-short-lived-user-sessions.md` | Use OIDC login and short-lived user session credentials. |
| `0011-api-error-contract.md` | Use a stable Problem Details error envelope. |
| `0012-web-client-and-separate-deployments.md` | Ship the web client in the monorepo but deploy it separately from the API over CORS. |
| `0013-serverless-aws-deployment-with-cdk.md` | Deploy serverless on AWS with CDK: API on Lambda, SPA on S3/CloudFront, an existing RDS, and SSM secrets read at runtime. |

## Template

```md
# ADR-XXXX: Title

Status: Accepted | Superseded | Proposed
Date: YYYY-MM-DD

## Context

## Decision

## Consequences

## Alternatives Considered

## Links
```
