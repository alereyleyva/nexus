from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from http import HTTPStatus

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette import status


class ProblemCode(StrEnum):
    bad_request = "BAD_REQUEST"
    unauthenticated = "UNAUTHENTICATED"
    authorization_denied = "AUTHORIZATION_DENIED"
    not_found = "NOT_FOUND"
    conflict = "CONFLICT"
    validation_failed = "VALIDATION_FAILED"
    rate_limited = "RATE_LIMITED"
    internal_error = "INTERNAL_ERROR"
    service_unavailable = "SERVICE_UNAVAILABLE"


class ProblemFieldError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    code: str
    message: str


class ProblemDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    status: int
    code: ProblemCode
    detail: str
    request_id: str
    errors: list[ProblemFieldError] | None = None
    retry_after_seconds: int | None = None


class ProjectError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: ProblemCode,
        title: str,
        detail: str,
        errors: Sequence[ProblemFieldError] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail
        self.errors = list(errors) if errors is not None else None


class BadRequestError(ProjectError):
    def __init__(self, detail: str = "The request is malformed.") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ProblemCode.bad_request,
            title="Bad request",
            detail=detail,
        )


class UnauthenticatedError(ProjectError):
    def __init__(self, detail: str = "Authentication is required.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ProblemCode.unauthenticated,
            title="Unauthenticated",
            detail=detail,
        )


class AuthorizationDeniedError(ProjectError):
    def __init__(self, detail: str = "The actor is not allowed to perform this operation.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ProblemCode.authorization_denied,
            title="Authorization denied",
            detail=detail,
        )


class NotFoundError(ProjectError):
    def __init__(self, resource: str = "resource") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ProblemCode.not_found,
            title="Not found",
            detail=f"The requested {resource} was not found.",
        )


class ConflictError(ProjectError):
    def __init__(
        self, detail: str = "The request conflicts with the current resource state."
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=ProblemCode.conflict,
            title="Conflict",
            detail=detail,
        )


class ValidationProblem(ProjectError):  # noqa: N818 - name is part of the ADR/spec terminology.
    def __init__(
        self,
        detail: str = "The request contains invalid fields.",
        *,
        errors: Sequence[ProblemFieldError] | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ProblemCode.validation_failed,
            title="Validation failed",
            detail=detail,
            errors=errors,
        )


class ServiceUnavailableError(ProjectError):
    def __init__(self, detail: str = "A required dependency is unavailable.") -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ProblemCode.service_unavailable,
            title="Service unavailable",
            detail=detail,
        )


def problem_response(error: ProjectError, request_id: str) -> JSONResponse:
    body = ProblemDetails(
        type=f"https://docs.nexus.local/problems/{error.code.value.lower().replace('_', '-')}",
        title=error.title,
        status=error.status_code,
        code=error.code,
        detail=error.detail,
        request_id=request_id,
        errors=error.errors,
    )
    headers: dict[str, str] = {}
    if error.status_code == HTTPStatus.UNAUTHORIZED:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=error.status_code,
        content=body.model_dump(mode="json", exclude_none=True),
        media_type="application/problem+json",
        headers=headers,
    )


async def project_error_handler(request: Request, exc: ProjectError) -> JSONResponse:
    return problem_response(exc, request_id=_request_id_from_request(request))


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors = [
        ProblemFieldError(
            field=".".join(str(part) for part in error["loc"] if part != "body"),
            code=str(error["type"]),
            message=str(error["msg"]),
        )
        for error in exc.errors()
    ]
    return problem_response(
        ValidationProblem(errors=field_errors),
        request_id=_request_id_from_request(request),
    )


async def unhandled_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    return problem_response(
        ProjectError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ProblemCode.internal_error,
            title="Internal error",
            detail="An unexpected server error occurred.",
        ),
        request_id=_request_id_from_request(request),
    )


def _request_id_from_request(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    header = request.headers.get("X-Request-Id")
    return header if header else "unknown"
