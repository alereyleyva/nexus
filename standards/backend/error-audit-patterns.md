# Error And Audit Patterns

## Purpose

This standard defines the implementation pattern for API errors and audit writes so behavior stays predictable across modules.

## Project Error Shape

Runtime code uses typed project exceptions. FastAPI handlers convert them to the Problem Details envelope from `specs/api/rest-api.md`.

Required concepts:

| Concept | Requirement |
| --- | --- |
| `ProblemCode` | Enum or literal set containing the stable API error codes. |
| `ProjectError` | Base exception with `status_code`, `code`, `title`, `detail`, and optional safe `errors`. |
| `ValidationProblem` | Used for normalized validation failures. |
| `NotFoundError` | Used both for missing and hidden resources. |
| `AuthorizationDeniedError` | Used when actor is authenticated and target is visible but operation is denied. |
| `ConflictError` | Used for idempotency mismatch, duplicate unique values, duplicate grants, and invalid lifecycle transitions. |

Rules:

| Rule | Requirement |
| --- | --- |
| No raw HTTPException | Do not raise `HTTPException` outside central error handling or narrow FastAPI infrastructure. |
| Safe detail | Error detail must not include secrets, raw tokens, full memory bodies, or cross-tenant existence hints. |
| Request id | Every error response includes request id. |
| Validation mapping | Pydantic validation errors map to `422 VALIDATION_FAILED`. |

## Audit Service Contract

`AuditService` owns audit persistence and safe metadata normalization.

Minimum method:

```python
def record_event(
    self,
    *,
    actor: ActorContext | None,
    action: AuditAction,
    resource_type: str | None,
    resource_id: UUID | None,
    decision: AuditDecision | None,
    reason: str | None,
    metadata: AuditMetadata,
) -> AuditEvent:
    ...
```

Rules:

| Rule | Requirement |
| --- | --- |
| Same transaction | Required audit events are written in the same service transaction as the sensitive operation. |
| Failure behavior | If the audit event cannot be persisted, the service operation fails and rolls back. |
| Metadata allowlist | Apply the allowlists in `specs/security/security-observability-audit.md`. |
| No raw credentials | Never pass raw tokens, auth codes, device codes, or refresh tokens to audit metadata. |
| Denial helper | Use one helper for authorization denials so audit reason codes stay stable. |

## Denial Pattern

When authorization fails:

1. Record `authorization.denied` with safe reason code.
2. Raise `NotFoundError` if revealing existence is unsafe.
3. Raise `AuthorizationDeniedError` if the resource is visible but the operation is denied.
4. Never include raw request bodies in metadata or error detail.

## Audit Actions

Audit action names are product constants. Use the exact strings from `specs/security/security-observability-audit.md`; do not construct action names dynamically.
