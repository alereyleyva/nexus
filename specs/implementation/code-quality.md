# Code Quality Spec

## Purpose

Nexus must be rebuildable from specs and maintainable by different developers and coding agents. Code quality tooling is part of the contract, not personal preference.

Ruff, basedpyright, tests, and coverage serve different purposes. A clean Ruff run does not prove type correctness. A clean type check does not prove formatting, lint, behavior, or coverage.

## Required Tooling

| Concern | Tool | Requirement |
| --- | --- | --- |
| Formatting | `ruff format` | The only Python formatter. Do not use Black separately. |
| Linting/imports | `ruff check` | The only Python linter and import sorter. Do not use isort separately. |
| Type checking | `basedpyright` | Required strict type checker. Must match Zed diagnostics. |
| Tests | `pytest` | Required test runner. |
| Coverage | `coverage.py` | Required coverage measurement. |
| Dependency locking | `uv` | Preferred Python package/dependency manager and lockfile owner. |

`mypy` is not part of the v1 quality stack. Use `basedpyright` so local editor diagnostics, CI, and agent verification agree.

## Canonical Commands

Run these from the repository root:

```sh
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest
uv run coverage run -m pytest
uv run coverage report
```

Developer convenience commands may wrap these, but CI must execute the same logical checks.

## Ruff Configuration Requirements

`pyproject.toml` must configure Ruff as follows unless an ADR changes it:

| Setting | Requirement |
| --- | --- |
| `target-version` | `py312`. |
| `line-length` | `100`. |
| formatter | `ruff format` defaults; no competing formatter. |
| imports | Ruff import sorting through rule family `I`. |
| unsafe fixes | Do not use `--unsafe-fixes` in CI or default scripts. |

Required lint rule families:

| Rule family | Purpose |
| --- | --- |
| `E`, `F`, `W` | pycodestyle/pyflakes correctness. |
| `I` | Import sorting. |
| `N` | Naming consistency. |
| `UP` | Modern Python syntax. |
| `B` | Bugbear correctness traps. |
| `SIM` | Simplification when it improves readability. |
| `C4` | Comprehension correctness/readability. |
| `PIE` | Common Python improvement rules. |
| `RET` | Return statement consistency. |
| `ARG` | Unused arguments. |
| `PTH` | Prefer `pathlib`. |
| `PT` | pytest style. |
| `S` | Security linting. |
| `RUF` | Ruff-specific correctness rules. |
| `DTZ` | Timezone-aware datetime usage. |
| `T20` | No `print` debugging in committed code. |
| `TRY` | Exception handling quality. |
| `PERF` | Low-risk performance traps. |

Allowed initial exceptions:

| Context | Exception |
| --- | --- |
| Tests | Ignore `S101` because plain `assert` is required in pytest. |
| Alembic migration versions | May ignore type-strictness in basedpyright, but still pass Ruff. |
| Intentional unused protocol args | Prefer a leading underscore before suppressing `ARG`. |

Do not enable mandatory docstring rules globally in v1. Public modules/classes/functions should still have docstrings when they clarify non-obvious behavior or contracts.

## basedpyright Configuration Requirements

`pyrightconfig.json` must exist at the repository root and be the source of truth for CI and Zed.

Required settings:

| Setting | Requirement |
| --- | --- |
| `typeCheckingMode` | `strict`. |
| `pythonVersion` | `3.12`. |
| `include` | `app`, `tests`, and `scripts` if present. |
| `exclude` | `.venv`, build/cache directories, and Alembic generated migration versions if strict checking is impractical. |
| `stubPath` | `typings` if local stubs are needed. |

Type policy:

| Rule | Requirement |
| --- | --- |
| Function boundaries | Public functions, service methods, repository methods, fixtures, and FastAPI dependencies must be typed. |
| `Any` | Avoid. Use `object`, protocols, typed dicts, Pydantic models, or explicit aliases instead. |
| Untyped third-party packages | Prefer typed alternatives, install stubs, or add minimal local stubs under `typings/`. |
| Suppressions | Use `# pyright: ignore[rule]` only with a specific rule and a reason nearby. |
| Global disables | Do not disable basedpyright rules globally to make CI pass. |

## Editor Consistency

Zed must use the same basedpyright configuration as CI. If Zed shows a basedpyright diagnostic that CI does not show, fix the project configuration rather than ignoring the editor.

Do not treat Ruff success as sufficient in editor workflows. Before considering a Python change done, run or satisfy both Ruff and basedpyright.

## Suppression Policy

| Suppression | Requirement |
| --- | --- |
| `# noqa` | Must name exact Ruff rule, for example `# noqa: TRY003`. |
| `# pyright: ignore[...]` | Must name exact basedpyright rule. |
| File-wide ignores | Forbidden unless documented in the relevant technical spec or ADR. |
| Permanent ignores | Should be rare; prefer fixing the design or typing the boundary. |

## Generated And External Code

Generated code must live in an explicitly named generated directory and be excluded or handled by documented tooling. Do not mix generated files into hand-written modules.

Alembic migration versions are generated-operational code: they must be readable, deterministic, and pass Ruff, but may be excluded from strict basedpyright if the generated shape is noisy.

## Definition Of Done For Python Changes

A Python code change is not done until:

| Check | Required outcome |
| --- | --- |
| Format | `ruff format --check .` passes. |
| Lint | `ruff check .` passes. |
| Types | `basedpyright` passes. |
| Tests | Relevant pytest tests pass. |
| Coverage | Coverage does not regress below the configured threshold. |
| Specs | Behavior or technical standards changed by the code are reflected in specs first. |
