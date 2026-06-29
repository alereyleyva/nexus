# CI Quality Gates Spec

## Purpose

CI must prove that the repository can be rebuilt from specs and that committed code satisfies formatting, linting, typing, tests, and coverage standards.

Local developer scripts may be convenient, but CI is the contract.

## Required Checks

CI must run these checks for every pull request and before merging to the main branch:

| Gate | Command |
| --- | --- |
| Formatting | `uv run ruff format --check .` |
| Linting/imports | `uv run ruff check .` |
| Type checking | `uv run basedpyright` |
| Tests | `uv run pytest` |
| Coverage | `uv run coverage run -m pytest && uv run coverage report` |
| Spec hygiene | `git diff --check` or equivalent whitespace check. |

Any failure blocks merge.

## Coverage Policy

Initial thresholds:

| Coverage | Threshold |
| --- | --- |
| Project line coverage | `85%` minimum. |
| Authorization/security modules | `95%` minimum. |
| New behavior | Must include meaningful tests even if global coverage stays above threshold. |

Coverage is a floor, not a substitute for behavior-first tests. A high-coverage test that does not prove authorization behavior is not sufficient.

## CI Configuration Requirements

| File | Requirement |
| --- | --- |
| `.github/workflows/ci.yml` | Runs all required checks. |
| `pyproject.toml` | Owns Ruff, pytest, coverage, and project metadata. |
| `pyrightconfig.json` | Owns basedpyright configuration used by CI and Zed. |
| `uv.lock` | Locks dependencies. CI must install from lockfile. |

## Execution Order

Recommended order:

1. Install dependencies from lockfile.
2. Run `ruff format --check .`.
3. Run `ruff check .`.
4. Run `basedpyright`.
5. Run tests with coverage.

Formatting and linting should fail fast before slower tests.

## Matrix

Initial CI may run only on Python 3.12 because Nexus targets Python 3.12. Add a version matrix only when the product explicitly supports more Python versions.

## Database In CI

Tests that exercise database behavior must use PostgreSQL, not SQLite, because tenant isolation, constraints, JSONB, FTS, and transaction behavior are PostgreSQL-specific.

The CI workflow should start PostgreSQL 16+ as a service and run Alembic migrations before integration tests once migrations exist.

## Agent And Developer Expectations

Before claiming a Python implementation task is complete, agents and developers should run the same logical gates locally or explain why a gate could not be run.

Do not merge code with known basedpyright errors because Ruff passed. Do not merge code with Ruff errors because basedpyright passed.

## Allowed Temporary Exceptions

Temporary CI exceptions require all of the following:

| Requirement | Detail |
| --- | --- |
| Explicit issue | Track the exception with a concrete follow-up. |
| Narrow scope | Disable only the smallest affected check/path/rule. |
| Time bound | Include expected removal condition. |
| Review | Require human approval. |

Permanent broad disables are not allowed.
