# ADR-0001: Modular Monolith API-First Product

Status: Accepted
Date: 2026-06-28

## Context

The product needs to validate governed shared memory quickly while preserving clear module boundaries for future growth. The product must enforce authentication, authorization, review workflow, search filtering, context pack filtering, and audit consistently.

Microservices would add deployment, observability, transaction, and authorization complexity before the product proves its core value.

## Decision

Build the product as an API-first modular monolith.

The recommended stack is Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL 16, pytest, ruff, mypy, and docker-compose.

Initial modules:

| Module | Responsibility |
| --- | --- |
| `identity` | Organizations, users, org memberships. |
| `auth` | OIDC login, auth sessions, short-lived access tokens, refresh rotation. |
| `groups` | Groups and group memberships. |
| `projects` | Projects, project memberships, timeline. |
| `authorization` | Policies and readable memory query. |
| `memory_entries` | Memory, evidence, grants, review, visibility. |
| `search` | Full text search. |
| `context_packs` | Structured memory packs. |
| `audit` | Audit events. |

## Consequences

The product is faster to implement and easier to test. Authorization logic can be centralized. Future extraction to services remains possible if load, deployment, or team boundaries justify it.

The monolith must still maintain module boundaries and avoid direct cross-module data access that bypasses authorization policies.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| Microservices from day one | Too much operational and coordination complexity for the product. |
| Database-first direct client access | Violates API authorization/audit boundary. |

## Links

| Spec | File |
| --- | --- |
| Architecture | `specs/product/overview.md` |
| API | `specs/api/rest-api.md` |
| SDD | `specs/implementation/spec-driven-development.md` |
