# Spec-Driven Development

## Purpose

This project should be implemented and maintained from specs. Specs define the product contract; code implements the contract; tests prove the contract; ADRs explain durable decisions.

## Core Rule

No behavior change should land without an aligned spec change, a test change, or an explicit note explaining why neither is required.

## Artifact Roles

| Artifact | Role |
| --- | --- |
| Markdown specs | Define product, domain, API, data, security, and operational requirements. |
| DBML | Defines the intended database model and relationships. |
| Gherkin features | Define behavior in acceptance-test language. |
| ADRs | Record significant decisions and rejected alternatives. |
| Tests | Executable proof that behavior matches specs. |
| Code | Implementation detail, not the source of product truth. |

## Change Workflow

| Step | Action |
| --- | --- |
| 1 | Identify the affected spec area. |
| 2 | Update Markdown spec, Gherkin scenario, DBML, or ADR first. |
| 3 | Implement the smallest code change that satisfies the spec. |
| 4 | Add or update tests mapped to the Gherkin scenario or invariant. |
| 5 | Run relevant tests. |
| 6 | If implementation reveals ambiguity, update `specs/implementation/open-questions.md` or create an ADR. |

## AI Agent Instructions

| Rule | Requirement |
| --- | --- |
| Build context first | Read relevant specs before editing code. |
| Prefer minimal implementation | Avoid adding future architecture not required by specs. |
| Do not invent permissions | All read paths must use the shared readable memory query. |
| Do not bypass the API boundary | No direct client access to database or derived indexes. |
| Keep product boundaries | No LLM, embeddings, sessions, repositories, agents-as-principals, or batches unless specs change. |
| Treat open questions as blockers | Do not silently choose product behavior listed in `specs/implementation/open-questions.md`. |

## Traceability Expectations

| Implementation artifact | Should reference |
| --- | --- |
| Permission tests | `specs/security/authorization.md` and relevant Gherkin scenario. |
| Database migrations | `specs/data/schema.dbml` and `specs/domain/model.md`. |
| API routes | `specs/api/rest-api.md`. |
| Search/context pack code | `specs/search/search-and-context-packs.md`. |
| Audit code | `specs/security/security-observability-audit.md`. |
| Architectural patterns | ADR IDs. |

## Gherkin-To-Test Mapping

Each scenario in `specs/features` should map to at least one automated test. Test names should include the behavior being proven, for example:

```text
test_search_does_not_return_project_memory_without_effective_project_access
test_context_pack_excludes_pending_review_by_default
test_cli_session_cannot_create_memory_above_max_visibility_scope
```

## ADR Policy

Create an ADR when deciding any of these:

| Area | Examples |
| --- | --- |
| Architecture | Monolith vs services, module boundaries, worker design. |
| Data | Source of truth, derived indexes, schema changes with long-term impact. |
| Security | Permission model, private access, token behavior, audit scope. |
| AI boundary | Whether API can call LLMs or generate embeddings. |
| Operational behavior | Retention, logs, metrics, failure handling, enterprise controls. |

## Spec Review Checklist

Before merging implementation work, check:

| Check | Required outcome |
| --- | --- |
| Relevant specs read | The PR or work item names affected specs. |
| No contradiction | Code does not violate ADRs or feature scenarios. |
| Tests updated | New behavior has automated coverage. |
| Security invariants | Authorization tests prove no new bypass. |
| Audit requirements | Sensitive operations are audited. |
| Open questions | No unresolved gap was implemented by assumption. |

## Maintenance Principle

Specs are living artifacts. They should be concise enough to use and strict enough to prevent accidental security or product drift.
