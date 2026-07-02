@core @memory @review
Feature: Memory creation and review workflow
  Memory can be created in different visibility scopes.
  Shared scopes may require human review before becoming active.

  Background:
    Given organization "acme" exists
    And active user "morgan" exists in organization "acme"
    And active user "riley" exists in organization "acme"
    And group "Backend Team" exists in organization "acme"
    And project "PAY" is owned by group "Backend Team"

  Scenario: Missing visibility defaults to private active memory
    Given "morgan" is an active organization member
    When "morgan" creates a memory entry without visibility scope
    Then the memory visibility scope is "private"
    And the memory status is "active"
    And the memory owner is "morgan"
    And an audit event "memory_entry.created" is emitted

  Scenario: Active user creates restricted memory as active
    Given "morgan" is an active organization member
    When "morgan" creates a "restricted" memory entry
    Then the memory status is "active"
    And the memory owner is "morgan"

  Scenario: Group member proposes group memory for review
    Given "morgan" is a "member" of group "Backend Team"
    When "morgan" creates a "group" memory entry visible to group "Backend Team"
    Then the memory status is "pending_review"
    And the response says review is required

  Scenario: Group lead creates group memory as active
    Given "riley" is a "lead" of group "Backend Team"
    When "riley" creates a "group" memory entry visible to group "Backend Team"
    Then the memory status is "active"
    And the response says review is not required

  Scenario: Project contributor proposes project memory for review
    Given "morgan" has effective project role "contributor" in project "PAY"
    When "morgan" creates a "project" memory entry for project "PAY"
    Then the memory status is "pending_review"
    And the response says review is required

  Scenario Outline: Project reviewer roles create project memory as active
    Given "riley" has effective project role "<role>" in project "PAY"
    When "riley" creates a "project" memory entry for project "PAY"
    Then the memory status is "active"
    And the response says review is not required

    Examples:
      | role       |
      | reviewer   |
      | maintainer |

  Scenario: Organization member proposes organization memory for review
    Given "morgan" has organization role "member"
    When "morgan" creates an "organization" memory entry
    Then the memory status is "pending_review"
    And the response says review is required

  Scenario: Knowledge admin creates organization memory as active
    Given "riley" has organization role "knowledge_admin"
    When "riley" creates an "organization" memory entry
    Then the memory status is "active"
    And the response says review is not required

  Scenario: Organization admin alone does not approve organization memory
    Given "morgan" has organization admin capability
    And "morgan" does not have organization role "knowledge_admin"
    When "morgan" creates an "organization" memory entry
    Then the memory status is "pending_review"

  Scenario: Creator cannot self-review shared memory
    Given "morgan" has effective project role "reviewer" in project "PAY"
    And "morgan" created a "pending_review" project memory entry in "PAY"
    When "morgan" approves the memory entry with comment "Approving my own proposal"
    Then the request is denied
    And an audit event "authorization.denied" is emitted

  Scenario: Project reviewer approves project memory
    Given "morgan" has effective project role "contributor" in project "PAY"
    And "morgan" created a "pending_review" project memory entry in "PAY"
    And "riley" has effective project role "reviewer" in project "PAY"
    When "riley" approves the memory entry with comment "Valid and useful"
    Then the memory status is "active"
    And the reviewed by user is "riley"
    And an audit event "memory_entry.approved" is emitted

  Scenario: Project reviewer rejects speculative project memory
    Given "morgan" created a "pending_review" project memory entry in "PAY"
    And "riley" has effective project role "reviewer" in project "PAY"
    When "riley" rejects the memory entry with comment "Too speculative"
    Then the memory status is "rejected"
    And an audit event "memory_entry.rejected" is emitted

  Scenario: Needs review memory can be reconfirmed
    Given a project memory entry in "PAY" has status "needs_review"
    And "riley" has effective project role "reviewer" in project "PAY"
    When "riley" approves the memory entry with comment "Still valid"
    Then the memory status is "active"

  Scenario: Active memory can be marked needs review
    Given a project memory entry in "PAY" has status "active"
    And "riley" has effective project role "reviewer" in project "PAY"
    When "riley" marks the memory entry as needs review
    Then the memory status is "needs_review"
    And an audit event "memory_entry.marked_needs_review" is emitted

  Scenario: Active memory can be deprecated
    Given a project memory entry in "PAY" has status "active"
    And "riley" has effective project role "reviewer" in project "PAY"
    When "riley" deprecates the memory entry
    Then the memory status is "deprecated"
    And an audit event "memory_entry.deprecated" is emitted

  Scenario: Project reviewer edits active project memory and it stays active
    Given a project memory entry in "PAY" has status "active"
    And "riley" has effective project role "reviewer" in project "PAY"
    When "riley" edits the memory entry body
    Then the memory status remains "active"
    And an audit event "memory_entry.updated" is emitted

  Scenario: Project contributor cannot edit active approved project memory
    Given a project memory entry in "PAY" has status "active"
    And "morgan" has effective project role "contributor" in project "PAY"
    When "morgan" edits the memory entry body
    Then the request is denied
    And the memory status remains "active"
    And an audit event "authorization.denied" is emitted

  Scenario: Deprecated memory can be archived
    Given a project memory entry in "PAY" has status "deprecated"
    And "riley" has effective project role "maintainer" in project "PAY"
    When "riley" archives the memory entry
    Then the memory status is "archived"
    And an audit event "memory_entry.archived" is emitted

  Scenario: API does not call LLM during memory creation
    Given "morgan" creates a memory entry submitted by source tool "codex"
    When the API persists the memory entry
    Then no LLM provider is called by the API
    And the source tool is recorded as "codex"
