# Agent Workflow Spec

## Purpose

Coding agents must treat Nexus as a spec-first project. The codebase should be rebuildable from specs, ADRs, DBML, Gherkin scenarios, and technical standards.

`AGENTS.md` is the operational entry point for agents. This spec is the canonical workflow it points to.

## Required Reading Flow

Before editing code, agents must read the smallest relevant set of specs:

| Task type | Required reading |
| --- | --- |
| Product/API behavior | `specs/api/rest-api.md`, relevant `specs/features/*.feature`, domain/security specs. |
| Authorization/security | `specs/security/authorization.md`, `specs/security/security-observability-audit.md`, relevant ADRs. |
| Database/schema | `specs/data/schema.dbml`, `specs/implementation/database-migrations.md`, domain spec. |
| Python implementation | `specs/implementation/repository-structure.md`, `python-style.md`, `code-quality.md`. |
| Tests | `specs/implementation/testing.md`, relevant Gherkin scenarios. |
| Tooling/CI | `code-quality.md`, `ci-quality-gates.md`, `dependency-management.md`. |

## Change Workflow

| Step | Requirement |
| --- | --- |
| 1 | Identify whether the requested change affects behavior, architecture, data, security, or technical standards. |
| 2 | Update the relevant spec/ADR/Gherkin/DBML first when the contract changes. |
| 3 | Implement the smallest code change that satisfies the updated contract. |
| 4 | Add or update behavior-first tests mapped to specs or Gherkin scenarios. |
| 5 | Run relevant quality gates. |
| 6 | Report what changed, what was verified, and any gates not run. |

## Non-Negotiable Rules

| Rule | Requirement |
| --- | --- |
| No invented behavior | Ask or update specs before choosing unspecified product behavior. |
| No hidden permissions | All memory read paths use shared readable/reviewable query rules. |
| No API bypass | Clients and internal routes must not bypass API/security boundaries. |
| No LLM in API | API does not call LLMs unless an ADR/spec changes this. |
| No silent tooling ignores | Do not add broad Ruff or basedpyright ignores. |
| No dependency sprawl | Add dependencies only when justified by specs. |
| No secret leakage | Never log or commit credentials, tokens, raw secrets, or secret-bearing bodies. |

## Implementation Expectations

| Area | Requirement |
| --- | --- |
| File placement | Follow `repository-structure.md`; do not create ad hoc utility folders. |
| Style | Follow `python-style.md`; keep routers thin and services explicit. |
| Quality | Follow `code-quality.md`; Ruff success is not enough without basedpyright. |
| CI | New code must be compatible with `ci-quality-gates.md`. |
| Migrations | Follow `database-migrations.md`; DBML and migrations move together. |

## Agent Output Expectations

When finishing a task, agents should report:

| Item | Requirement |
| --- | --- |
| Changed specs/code | Concise list of important files. |
| Tests/checks | Commands run and results. |
| Not run | Any skipped check and why. |
| Residual risk | Known gaps or follow-up if relevant. |

Do not over-explain obvious edits, but do not hide verification gaps.

## Commit Expectations

When asked to commit, agents must:

| Rule | Requirement |
| --- | --- |
| Inspect first | Review status, diff, staged diff, and recent log. |
| Atomic commits | Group by functional intent. |
| Conventional commits | Use `docs:`, `feat:`, `fix:`, `test:`, etc. |
| No blind staging | Do not use `git add .` when unrelated changes may exist. |
| No attribution noise | Do not add co-author or AI tool credits. |
