# syntax=docker/dockerfile:1

# Production image for the Nexus API (FastAPI + SQLAlchemy, Python 3.12).
# Migrations are intentionally NOT run here; run `alembic upgrade head` as a
# separate deploy step (see standards/deployment.md and docker-compose.prod.yml).

########################################
# Stage 1 — builder: resolve deps with uv
########################################
FROM python:3.12-slim AS builder

# uv binary from the official Astral image.
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install the locked production dependencies into /app/.venv. The project itself
# is not packaged (no [build-system]); the app runs from source on PYTHONPATH,
# matching pyproject.toml `pythonpath = ["."]`.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev --no-install-project

########################################
# Stage 2 — runtime: minimal non-root image
########################################
FROM python:3.12-slim AS runtime

# curl is used by the container HEALTHCHECK.
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 nexus \
    && useradd --system --uid 1001 --gid nexus --home-dir /app --no-create-home nexus

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Virtual environment from the builder, then the application source.
COPY --from=builder --chown=nexus:nexus /app/.venv /app/.venv
COPY --chown=nexus:nexus alembic.ini ./alembic.ini
COPY --chown=nexus:nexus app ./app

USER nexus

EXPOSE 8000

# Readiness probe checks DB connectivity via /health/ready.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health/ready || exit 1

# Production server: uvicorn with multiple workers (stateless API, safe to scale).
# Tune worker count with UVICORN_WORKERS at deploy time if desired.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
