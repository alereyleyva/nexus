from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.common.errors import (
    ProjectError,
    ServiceUnavailableError,
    project_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.common.logging import configure_logging
from app.common.time import utc_now
from app.config import get_settings
from app.db.session import SessionLocal, check_ready
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.context_packs.router import router as context_packs_router
from app.modules.memory_entries.router import router as memory_entries_router
from app.modules.projects.router import router as projects_router
from app.modules.search.router import router as search_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="Nexus API", version=settings.version)

    async def handle_project_error(request: Request, exc: Exception) -> Response:
        if isinstance(exc, ProjectError):
            return await project_error_handler(request, exc)
        return await unhandled_error_handler(request, exc)

    async def handle_validation_error(request: Request, exc: Exception) -> Response:
        if isinstance(exc, RequestValidationError):
            return await validation_error_handler(request, exc)
        return await unhandled_error_handler(request, exc)

    app.add_exception_handler(ProjectError, handle_project_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
    app.include_router(auth_router)
    app.include_router(memory_entries_router)
    app.include_router(search_router)
    app.include_router(context_packs_router)
    app.include_router(projects_router)
    app.include_router(admin_router)

    @app.middleware("http")
    async def request_id_middleware(  # pyright: ignore[reportUnusedFunction]
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.request_id = request.headers.get("X-Request-Id", "unknown")
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.service_name,
            "version": settings.version,
            "time": utc_now().astimezone(UTC).isoformat().replace("+00:00", "Z"),
        }

    @app.get("/health/live")
    def live() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return health()

    @app.get("/health/ready")
    def ready() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        db: Session = SessionLocal()
        try:
            check_ready(db)
        except Exception as exc:
            raise ServiceUnavailableError() from exc
        finally:
            db.close()
        return health()

    return app


app = create_app()
