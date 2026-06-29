# Python Style Spec

## Purpose

This standard defines how Python code should be written in Nexus. It complements `standards/backend/repository-structure.md`, `standards/backend/internal-services.md`, and `standards/python/code-quality.md`.

The goal is boring, explicit, typed, maintainable code that new developers and agents can navigate quickly.

## Language Baseline

| Rule | Requirement |
| --- | --- |
| Python version | Use Python 3.12 syntax and standard library features. |
| Typing syntax | Use built-in generics such as `list[str]`, `dict[str, object]`, and `X | None`. |
| Datetimes | Use timezone-aware UTC datetimes. Do not use naive `datetime.utcnow()`. |
| Paths | Use `pathlib.Path`, not string path manipulation. |
| JSON-like values | Prefer typed Pydantic models or `TypedDict` at boundaries. |

## Naming

| Item | Convention |
| --- | --- |
| Modules/packages | `snake_case`. |
| Classes | `PascalCase`. |
| Functions/methods | `snake_case` verb phrases. |
| Variables | `snake_case` nouns. |
| Constants | `UPPER_SNAKE_CASE`. |
| SQLAlchemy models | Singular domain noun, for example `MemoryEntry`. |
| Pydantic request models | Verb/object plus `Request`, for example `CreateMemoryEntryRequest`. |
| Pydantic response models | Object plus `Response`, for example `MemoryEntryResponse`. |
| Internal command/result DTOs | Domain action plus `Command`, `Result`, or `Decision`. |

Names should encode product language from `specs/domain/model.md`. Do not invent synonyms such as `note_item` for `memory_entry`.

## Imports

| Rule | Requirement |
| --- | --- |
| Absolute imports | Use imports rooted at `app`, for example `from app.modules.memory_entries.service import MemoryEntryService`. |
| Relative imports | Avoid except inside tightly coupled test packages if needed. |
| Import sorting | Ruff owns sorting. Do not hand-format import groups. |
| Import cycles | Forbidden. Fix boundaries instead of hiding cycles with local imports. |
| Type-only imports | Use `from __future__ import annotations` in Python modules and `if TYPE_CHECKING` when needed. |

## Module Boundaries

| Layer | May import |
| --- | --- |
| `router.py` | Module schemas, service interfaces, FastAPI dependencies, common errors. |
| `service.py` | Module repositories, other services through explicit constructor injection, domain schemas/DTOs. |
| `repository.py` | SQLAlchemy models and database session types. |
| `models.py` | SQLAlchemy base/types and local enum/value definitions. |
| `schemas.py` | Pydantic, domain enums/value objects, standard library. |
| `authorization` | Domain models, roles, readable query helpers, no routers. |
| `common` | No imports from `app.modules.*`. |

Forbidden dependencies:

| Dependency | Reason |
| --- | --- |
| Repository importing router | Inverts API and persistence layers. |
| Repository making authorization decisions | Authorization must stay centralized. |
| Router querying database directly | Bypasses service policies and audit. |
| Search/context code bypassing readable query | Security leak risk. |
| `common` importing product modules | Creates hidden coupling and cycles. |

## FastAPI Rules

| Rule | Requirement |
| --- | --- |
| Routers are thin | Parse input, call service, return response. No business workflows. |
| Dependencies | Shared request dependencies live in `app/dependencies.py` or focused module dependencies. |
| Response models | Every endpoint has an explicit response schema unless returning `204`. |
| Error responses | Raise project errors that map to the common Problem Details envelope. |
| Auth | Protected endpoints resolve `ActorContext` before service calls. |
| Background work | Do not add background workers until specified. Keep side effects transactional where possible. |

## Pydantic Rules

| Rule | Requirement |
| --- | --- |
| Version | Use Pydantic v2. |
| Request schemas | Forbid unknown fields unless a spec explicitly allows flexible metadata. |
| Response schemas | Avoid leaking internal DB-only fields. |
| Flexible JSON | Use explicit fields such as `source_context` and `metadata`; validate known structure when possible. |
| Config | Prefer explicit `model_config = ConfigDict(...)` for non-default behavior. |
| Validation | Keep cross-field validation close to request schemas when it is API-shape validation. Domain policy stays in services. |

## SQLAlchemy Rules

| Rule | Requirement |
| --- | --- |
| Version | Use SQLAlchemy 2 style. |
| Models | Models belong to their owning module unless shared by design. |
| Session ownership | Request/session lifecycle is managed centrally, not inside repositories. |
| Queries | Complex query builders should be named and tested. |
| Tenant safety | Tenant-owned queries must include `org_id` filtering or derive from authorized base queries. |
| Transactions | Services define transaction boundaries. Repositories do not commit independently. |

## Service Rules

| Rule | Requirement |
| --- | --- |
| Business logic | Lives in services, not routers or repositories. |
| Authorization | Services call `AuthorizationService` before sensitive reads/writes. |
| Audit | Services call `AuditService` in the same workflow for sensitive operations. |
| Return values | Use typed result objects for non-trivial decisions, not ad hoc dictionaries. |
| Side effects | Make side effects explicit in method names or result types. |

## Error Handling

| Rule | Requirement |
| --- | --- |
| Domain errors | Raise typed project exceptions, not raw `HTTPException` outside routers/common handlers. |
| Error details | Never include secrets, raw credentials, or full request bodies. |
| Not found vs denied | Follow `specs/api/rest-api.md`; inaccessible resources may return `404` while still auditing denial. |
| Unexpected errors | Let centralized handlers convert them to `INTERNAL_ERROR` and log request id. |

## Logging

| Rule | Requirement |
| --- | --- |
| Use logging | Do not use `print`. |
| Request id | Include request id in request logs and audit metadata. |
| Secrets | Never log access tokens, refresh tokens, authorization codes, raw search queries, or full memory bodies by default. |
| Structure | Prefer structured key/value metadata over interpolated blobs. |

## Tests

| Rule | Requirement |
| --- | --- |
| Behavior first | Test names should describe behavior, not implementation details. |
| Fixtures | Keep fixtures explicit and typed. Avoid global magic setup. |
| Factories | Use small factories/builders for repeated domain objects. |
| Assertions | Use plain `assert`. |
| Time | Freeze or inject time for deterministic lifecycle tests. |
| Database | Tests that need persistence should prove tenant isolation and authorization behavior. |
