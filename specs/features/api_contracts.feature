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

  Scenario: Bulk create is atomic when one entry is invalid
    Given "pablo" can create project memory in "CECW"
    When "pablo" posts one valid entry and one invalid entry to "POST /v1/memory-entries:bulk"
    Then the request is rejected with validation failure
    And no memory entries are created

  Scenario: GET memory uses readable memory query
    Given "pablo" cannot read a memory entry
    When "pablo" calls "GET /v1/memory-entries/{id}"
    Then the request is denied
    And the same memory entry would not appear in search

  Scenario: API errors use the common problem envelope
    Given "pablo" sends an invalid create memory request
    When the API returns a validation error
    Then the response content type is "application/problem+json"
    And the response contains stable error code "VALIDATION_FAILED"
    And the response contains the request id

  Scenario: Memory list uses cursor pagination
    Given "pablo" can read more than 50 memory entries in project "CECW"
    When "pablo" lists memory entries with limit 50
    Then the response includes at most 50 items
    And the response includes page metadata
    And the next page does not include unauthorized memory

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

  Scenario: Review queue only returns reviewable memory
    Given "pablo" can review one pending project memory entry in "CECW"
    And "pablo" cannot review another pending organization memory entry
    When "pablo" calls "GET /v1/review-queue"
    Then the response includes the project memory entry
    And the response excludes the organization memory entry

  Scenario: Archive endpoint hides memory from normal search
    Given "pablo" can archive an active project memory entry in "CECW"
    When "pablo" calls "POST /v1/memory-entries/{id}/archive"
    Then the memory entry status becomes "archived"
    And the memory entry is absent from normal search results
    And an audit event "memory_entry.archived" is emitted

  Scenario: Soft delete is denied for active shared memory
    Given "pablo" can control an active shared project memory entry in "CECW"
    When "pablo" calls "DELETE /v1/memory-entries/{id}"
    Then the request is rejected with conflict
    And the response tells the client to archive instead

  Scenario: Healthcheck returns liveness without authentication
    When an unauthenticated client calls "GET /health"
    Then the response status is 200
    And the response body status is "ok"

  Scenario: Organization admin configures project membership through admin API
    Given "pablo" has organization admin capability
    When "pablo" sets "fabio" as "reviewer" in project "CECW"
    Then the project membership is stored
    And an audit event "admin.project_membership_changed" is emitted

  Scenario: Organization admin cannot use admin capability to read private memory
    Given "pablo" has organization admin capability
    And "fabio" owns a private memory entry
    When "pablo" calls "GET /v1/memory-entries/{id}" for that memory
    Then the request is denied
    And an audit event "authorization.denied" is emitted

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
