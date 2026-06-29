# Dependency Management Spec

## Purpose

Dependencies define long-term maintenance and security cost. Nexus should stay small, explicit, and reproducible.

## Tooling

| Concern | Requirement |
| --- | --- |
| Package manager | Use `uv` for dependency resolution, virtualenv management, and lockfile generation. |
| Project metadata | Store project config in `pyproject.toml`. |
| Lockfile | Commit `uv.lock`. |
| Python version | Require Python `>=3.12,<3.13` until a spec expands support. |

## Dependency Groups

Use explicit dependency groups:

| Group | Contents |
| --- | --- |
| Runtime | FastAPI, ASGI server, SQLAlchemy, Alembic, PostgreSQL driver, Pydantic/settings, auth/crypto libraries. |
| Dev | Ruff, basedpyright, pytest, coverage, HTTP test clients, local tooling. |
| Optional/future | Only when a feature spec requires it. |

Do not import dev-only dependencies from runtime code.

## Adding Dependencies

Before adding a dependency, verify:

| Question | Requirement |
| --- | --- |
| Is stdlib enough? | Prefer standard library for simple needs. |
| Is it product-required? | Tie dependency to a spec, ADR, or concrete implementation need. |
| Is it maintained? | Recent releases, active issue handling, compatible license. |
| Is it typed? | Prefer packages with `py.typed` or available stubs. |
| Is it secure? | Avoid packages with known unresolved critical vulnerabilities. |
| Is it small? | Avoid large frameworks for narrow tasks. |

If a package lacks types, document the mitigation: stubs package, local `typings/`, or a typed wrapper boundary.

## Versioning

| Rule | Requirement |
| --- | --- |
| Direct dependencies | Specify sensible lower and upper bounds in `pyproject.toml`. |
| Transitive dependencies | Managed by `uv.lock`; do not import transitive dependencies directly. |
| Updates | Update intentionally and review changelogs for runtime/security-sensitive packages. |
| Security updates | Prioritize auth, crypto, web, database, and parser dependencies. |

## Dependency Boundaries

| Rule | Requirement |
| --- | --- |
| External SDKs | Wrap behind module services/adapters. Do not leak SDK types across the app. |
| Auth providers | Keep Google/OIDC provider details behind the auth module. |
| Future vector/AI providers | Do not add until specs and ADRs allow them. |
| Test helpers | Keep test-only factories/helpers under `tests/`. |

## Reproducibility

CI must install from `uv.lock`. A dependency change is incomplete unless `pyproject.toml` and `uv.lock` are updated together.

Do not commit local virtualenvs, build artifacts, caches, downloaded wheels, or generated vendor directories.
