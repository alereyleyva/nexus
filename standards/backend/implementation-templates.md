# Backend Implementation Templates

## Purpose

This standard removes implementation degrees of freedom for Python/FastAPI backend code. When building a module, follow these templates unless a more specific spec or ADR says otherwise.

## Execution Model

| Concern | Decision |
| --- | --- |
| FastAPI handlers | Synchronous `def` route functions. |
| Database access | Synchronous SQLAlchemy 2 `Session`. |
| Async database access | Not used in v1. Do not mix `AsyncSession` into app code. |
| Request session | One DB session per request from `app/dependencies.py`. |
| Transactions | Services own write transaction boundaries. |

## Module Files

Each domain module uses only the files it needs from this shape:

```text
app/modules/<module_name>/
  __init__.py
  models.py
  schemas.py
  repository.py
  service.py
  router.py
```

Optional files must have precise ownership: `queries.py`, `types.py`, `policies.py`, `adapters.py`, or `exceptions.py`.

## Router Template

```python
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_actor_context, get_db_session
from app.modules.auth.types import ActorContext

from .schemas import ResourceResponse
from .service import ResourceService

router = APIRouter(prefix="/v1/resources", tags=["resources"])


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(
    resource_id: UUID,
    db: Session = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
) -> ResourceResponse:
    service = ResourceService(db)
    return service.get_resource(actor=actor, resource_id=resource_id)
```

Rules:

| Rule | Requirement |
| --- | --- |
| Router responsibilities | Parse HTTP inputs, resolve dependencies, call service, return schema. |
| No business logic | Routers do not branch on domain policy except HTTP dependency wiring. |
| No direct persistence | Routers do not import SQLAlchemy models or repositories. |
| Response model | Every non-204 endpoint has an explicit response schema. |

## Service Template

```python
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.types import ActorContext

from .repository import ResourceRepository
from .schemas import ResourceResponse


class ResourceService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = ResourceRepository(db)

    def get_resource(self, *, actor: ActorContext, resource_id: UUID) -> ResourceResponse:
        resource = self._repository.get_by_id_for_org(
            org_id=actor.org_id,
            resource_id=resource_id,
        )
        if resource is None:
            raise_not_found("resource")
        return ResourceResponse.model_validate(resource)
```

Rules:

| Rule | Requirement |
| --- | --- |
| Business workflows | Services own authorization, transactions, audit orchestration, and response mapping. |
| Constructor injection | Use explicit constructor dependencies. Avoid global service locators. |
| Errors | Services raise project exceptions, not `HTTPException`. |
| Writes | Use `with self._db.begin():` for write workflows unless the request dependency already owns an explicit transaction contract. |
| Flush/refresh | Services call `flush()` when generated ids are needed before audit/evidence rows. Use `refresh()` only when server-generated values are required in the response. |

## Repository Template

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Resource


class ResourceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_org(self, *, org_id: UUID, resource_id: UUID) -> Resource | None:
        statement = select(Resource).where(
            Resource.org_id == org_id,
            Resource.id == resource_id,
        )
        return self._db.execute(statement).scalar_one_or_none()
```

Rules:

| Rule | Requirement |
| --- | --- |
| Return values | Return ORM objects, scalar values, or `None`; do not raise HTTP/project errors for normal misses. |
| No commits | Repositories never call `commit()`, `rollback()`, or `begin()`. |
| No authorization decisions | Repositories may apply tenant filters but do not decide permissions. |
| Method names | Prefer `get_by_id_for_org`, `list_page`, `exists_*`, `add`, `delete`, and `lock_*_for_update`. |

## Schema Template

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateResourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
```

Rules:

| Rule | Requirement |
| --- | --- |
| Requests | `extra="forbid"` unless a spec explicitly allows flexible metadata. |
| Responses | `from_attributes=True` when mapping ORM objects. |
| Commands/results | Use typed Pydantic models or dataclasses; do not pass ad hoc dictionaries between layers. |

## Model Template

SQLAlchemy models follow DBML order:

1. Primary key.
2. Tenant key `org_id` when present.
3. Required foreign keys.
4. Domain fields.
5. Lifecycle timestamps.
6. Indexes and constraints.

DBML-backed enum values must be represented once in the owning module and reused by schemas/services. Do not duplicate raw enum strings across modules.

## Memory Read Rule

Any query returning memory entries to a client must compose from `authorization/readable_queries.py` or `authorization/reviewable_queries.py`. Direct `select(MemoryEntry)` client-read paths outside those query builders are forbidden.
