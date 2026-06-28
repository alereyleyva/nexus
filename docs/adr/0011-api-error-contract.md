# ADR-0011: API Error Contract

Status: Accepted
Date: 2026-06-28

## Context

Nexus will have UI, CLI, and future integration clients. Those clients need stable error handling that does not depend on framework defaults or ad hoc response bodies.

Errors also need to be safe for security-sensitive cases such as authentication failures, authorization denials, validation failures, and not-found responses that might otherwise reveal resource existence.

## Decision

Use a single JSON error envelope for all non-2xx API responses. The envelope is based on RFC 9457 Problem Details and returned as `application/problem+json`.

Required fields:

| Field | Requirement |
| --- | --- |
| `type` | Stable URI for the problem class. |
| `title` | Short human-readable summary. |
| `status` | HTTP status code. |
| `code` | Stable machine-readable Nexus error code. |
| `detail` | Safe human-readable detail. Must not include secrets. |
| `request_id` | Request correlation id. |

Optional fields:

| Field | Requirement |
| --- | --- |
| `errors` | Field-level validation or conflict details. |
| `retry_after_seconds` | Present for retryable throttling or dependency failures when known. |

Example:

```json
{
  "type": "https://docs.nexus.local/problems/validation-failed",
  "title": "Validation failed",
  "status": 422,
  "code": "VALIDATION_FAILED",
  "detail": "The request contains invalid fields.",
  "request_id": "req_01J...",
  "errors": [
    {
      "field": "visibility_scope",
      "code": "required",
      "message": "visibility_scope is required"
    }
  ]
}
```

Status code and error-code choices are part of the public API contract. Details may change for clarity, but clients should branch on HTTP status and `code`, not on `detail`.

Unauthorized resource reads may return `404 NOT_FOUND` instead of `403 AUTHORIZATION_DENIED` when revealing resource existence would leak information. The denial must still be audited internally.

## Consequences

Clients get stable behavior across endpoints. The API can centrally handle validation, authentication, authorization, idempotency conflicts, rate limits, and unexpected failures.

Implementation should define common error classes in `app/common/errors.py` and a single exception handler layer in FastAPI.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| Framework default errors | Inconsistent across validation, auth, and domain errors. |
| Free-form `{ "error": "..." }` responses | Not expressive enough for field errors and stable client branching. |
| Endpoint-specific error envelopes | Increases client complexity and documentation drift. |

## Links

| Spec | File |
| --- | --- |
| API | `specs/api/rest-api.md` |
| Testing | `specs/implementation/testing.md` |
