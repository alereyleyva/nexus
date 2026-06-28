@core @ui @cli
Feature: Minimal UI and CLI behavior
  UI and CLI clients use the API, respect review workflow, and never bypass authorization.

  Background:
    Given organization "aircury" exists
    And project "CECW" exists in organization "aircury"
    And active user "pablo" exists in organization "aircury"

  Scenario: Project Memory view filters authorized memory
    Given "pablo" can read multiple memory entries in project "CECW"
    When "pablo" filters Project Memory by type "decision" and tag "payments"
    Then the UI requests authorized memory through the API
    And the UI shows only matching authorized memory

  Scenario: Review Queue shows pending memory review details
    Given "pablo" can review a pending project memory entry
    When "pablo" opens the Review Queue
    Then the UI shows title, type, body, rationale, evidence, confidence, owner, source tool, and proposed scope
    And the UI offers approve and reject actions

  Scenario: Memory Detail shows audit and source context
    Given "pablo" can read a memory entry with evidence and source context
    When "pablo" opens Memory Detail
    Then the UI shows content, status, visibility, project, owner, evidence, source context, and audit timeline

  Scenario: Search UI uses authorized search endpoint
    Given "pablo" searches for "payment retries"
    When the UI executes the search
    Then the UI calls "POST /v1/search"
    And the UI does not access PostgreSQL or indexes directly

  Scenario: Context Pack UI displays grouped result
    Given "pablo" can generate context packs for project "CECW"
    When "pablo" requests a context pack for task "Continue payment sync retries"
    Then the UI calls "POST /v1/context-packs"
    And the UI displays decisions, problems, solutions, failed attempts, risks, procedures, and open questions

  Scenario: CLI creates memory with source metadata
    Given "pablo" completed "nexus login" and has a CLI session with capability "memory:create"
    When the CLI submits a memory entry from source tool "codex"
    Then the API receives source tool "codex"
    And the API receives source context when available
    And the API receives client entry id when available

  Scenario: CLI respects pending review response
    Given "pablo" has effective project role "contributor" in project "CECW"
    When the CLI submits project memory
    Then the CLI receives status "pending_review"
    And the CLI communicates that review is required

  Scenario: CLI renders context pack locally
    Given "pablo" calls the context pack API through the CLI
    When the API returns structured JSON
    Then the CLI may render Markdown locally
    And the API does not call an LLM for rendering
