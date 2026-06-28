@core @api
Feature: API contracts
  The REST API accepts structured memory entries and returns authorized memory, search results, context packs, and project timeline events.

  Background:
    Given organization "aircury" exists
    And active user "pablo" exists in organization "aircury"
    And project "CECW" exists in organization "aircury"

  Scenario: Create memory stores source context and evidence
    Given "pablo" can create private memory
    When "pablo" posts a memory entry with source context and one evidence item
    Then a memory entry is created
    And the source context is stored as JSON
    And the evidence item is stored
    And the evidence inherits memory visibility

  Scenario: Create memory records source tool as source, not actor
    Given "pablo" posts a memory entry with source tool "codex"
    When the memory entry is created
    Then the created by user is "pablo"
    And the source tool is "codex"
    And audit describes that "pablo" created memory using "codex"

  Scenario: Client entry id makes create idempotent
    Given "pablo" created a memory entry with source tool "codex" and client entry id "local-memory-001"
    When "pablo" retries the same create request with client entry id "local-memory-001"
    Then no duplicate memory entry is created
    And the API returns the existing memory entry

  Scenario: Bulk create creates independent entries
    Given "pablo" can create project memory in "CECW"
    When "pablo" posts two entries to "POST /v1/memory-entries:bulk"
    Then two independent memory entries are created
    And no capture batch resource is created
    And each memory entry has its own status

  Scenario: GET memory uses readable memory query
    Given "pablo" cannot read a memory entry
    When "pablo" calls "GET /v1/memory-entries/{id}"
    Then the request is denied
    And the same memory entry would not appear in search

  Scenario: PATCH memory updates search vector
    Given "pablo" can edit a memory entry
    When "pablo" changes the memory title and tags
    Then the memory entry is updated
    And the search vector is refreshed
    And an audit event "memory_entry.updated" is emitted

  Scenario: Review endpoint records review metadata
    Given "pablo" can approve a pending memory entry
    When "pablo" posts decision "approve" with review comment "Valid"
    Then the memory entry status becomes "active"
    And reviewed by user is "pablo"
    And reviewed at is set
    And review comment is "Valid"

  Scenario: Timeline only returns authorized project memory events
    Given project "CECW" has one memory event "fabio" can read
    And project "CECW" has one private memory event "fabio" cannot read
    When "fabio" calls "GET /v1/projects/{project_id}/timeline"
    Then the timeline includes the authorized event
    And the timeline excludes the private event

  Scenario: Source context supports non-code sources
    Given "pablo" posts a memory entry with meeting source context
    When the memory entry is created
    Then the source context can include meeting title, date, and participants
    And no meetings table is required in the product

  Scenario: CLI cannot assume shared memory becomes active
    Given "pablo" has effective project role "contributor" in project "CECW"
    When the CLI submits project memory
    Then the API response status is "pending_review"
    And the API response says review is required
