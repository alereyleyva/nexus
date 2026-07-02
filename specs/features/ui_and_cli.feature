@core @ui @cli
Feature: Minimal UI and CLI behavior
  UI and CLI clients use the API, respect review workflow, and never bypass authorization.

  Background:
    Given organization "acme" exists
    And project "PAY" exists in organization "acme"
    And active user "morgan" exists in organization "acme"

  Scenario: Project Memory view filters authorized memory
    Given "morgan" can read multiple memory entries in project "PAY"
    When "morgan" filters Project Memory by type "decision" and tag "payments"
    Then the UI requests authorized memory through the API
    And the UI shows only matching authorized memory

  Scenario: Review Queue shows pending memory review details
    Given "morgan" can review a pending project memory entry
    When "morgan" opens the Review Queue
    Then the UI shows title, type, body, rationale, evidence, confidence, owner, source tool, and proposed scope
    And the UI offers approve and reject actions

  Scenario: Memory Detail shows audit and source context
    Given "morgan" can read a memory entry with evidence and source context
    When "morgan" opens Memory Detail
    Then the UI shows content, status, visibility, project, owner, evidence, source context, and audit timeline

  Scenario: Search UI uses authorized search endpoint
    Given "morgan" searches for "payment retries"
    When the UI executes the search
    Then the UI calls "POST /v1/search"
    And the UI does not access PostgreSQL or indexes directly

  Scenario: Context Pack UI displays grouped result
    Given "morgan" can generate context packs for project "PAY"
    When "morgan" requests a context pack for task "Continue payment sync retries"
    Then the UI calls "POST /v1/context-packs"
    And the UI displays decisions, problems, solutions, failed attempts, risks, procedures, and open questions

  Scenario: CLI creates memory with source metadata
    Given "morgan" completed "nexus login" and has a CLI session with capability "memory:create"
    When the CLI submits a memory entry from source tool "codex"
    Then the API receives source tool "codex"
    And the API receives source context when available
    And the API receives client entry id when available

  Scenario: CLI respects pending review response
    Given "morgan" has effective project role "contributor" in project "PAY"
    When the CLI submits project memory
    Then the CLI receives status "pending_review"
    And the CLI communicates that review is required

  Scenario: CLI renders context pack locally
    Given "morgan" calls the context pack API through the CLI
    When the API returns structured JSON
    Then the CLI may render Markdown locally
    And the API does not call an LLM for rendering
