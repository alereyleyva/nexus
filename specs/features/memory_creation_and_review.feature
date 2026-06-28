@core @memory @review
Feature: Memory creation and review workflow
  Memory can be created in different visibility scopes.
  Shared scopes may require human review before becoming active.

  Background:
    Given organization "aircury" exists
    And active user "pablo" exists in organization "aircury"
    And active user "fabio" exists in organization "aircury"
    And group "Backend Team" exists in organization "aircury"
    And project "CECW" is owned by group "Backend Team"

  Scenario: Missing visibility defaults to private active memory
    Given "pablo" is an active organization member
    When "pablo" creates a memory entry without visibility scope
    Then the memory visibility scope is "private"
    And the memory status is "active"
    And the memory owner is "pablo"
    And an audit event "memory_entry.created" is emitted

  Scenario: Active user creates restricted memory as active
    Given "pablo" is an active organization member
    When "pablo" creates a "restricted" memory entry
    Then the memory status is "active"
    And the memory owner is "pablo"

  Scenario: Group member proposes group memory for review
    Given "pablo" is a "member" of group "Backend Team"
    When "pablo" creates a "group" memory entry visible to group "Backend Team"
    Then the memory status is "pending_review"
    And the response says review is required

  Scenario: Group lead creates group memory as active
    Given "fabio" is a "lead" of group "Backend Team"
    When "fabio" creates a "group" memory entry visible to group "Backend Team"
    Then the memory status is "active"
    And the response says review is not required

  Scenario: Project contributor proposes project memory for review
    Given "pablo" has effective project role "contributor" in project "CECW"
    When "pablo" creates a "project" memory entry for project "CECW"
    Then the memory status is "pending_review"
    And the response says review is required

  Scenario Outline: Project reviewer roles create project memory as active
    Given "fabio" has effective project role "<role>" in project "CECW"
    When "fabio" creates a "project" memory entry for project "CECW"
    Then the memory status is "active"
    And the response says review is not required

    Examples:
      | role       |
      | reviewer   |
      | maintainer |

  Scenario: Organization member proposes organization memory for review
    Given "pablo" has organization role "member"
    When "pablo" creates an "organization" memory entry
    Then the memory status is "pending_review"
    And the response says review is required

  Scenario: Knowledge admin creates organization memory as active
    Given "fabio" has organization role "knowledge_admin"
    When "fabio" creates an "organization" memory entry
    Then the memory status is "active"
    And the response says review is not required

  Scenario: Org admin alone does not approve organization memory
    Given "pablo" has organization role "org_admin"
    And "pablo" does not have organization role "knowledge_admin"
    When "pablo" creates an "organization" memory entry
    Then the memory status is "pending_review"

  Scenario: Project reviewer approves project memory
    Given "pablo" has effective project role "contributor" in project "CECW"
    And "pablo" created a "pending_review" project memory entry in "CECW"
    And "fabio" has effective project role "reviewer" in project "CECW"
    When "fabio" approves the memory entry with comment "Valid and useful"
    Then the memory status is "active"
    And the reviewed by user is "fabio"
    And an audit event "memory_entry.approved" is emitted

  Scenario: Project reviewer rejects speculative project memory
    Given "pablo" created a "pending_review" project memory entry in "CECW"
    And "fabio" has effective project role "reviewer" in project "CECW"
    When "fabio" rejects the memory entry with comment "Too speculative"
    Then the memory status is "rejected"
    And an audit event "memory_entry.rejected" is emitted

  Scenario: Needs review memory can be reconfirmed
    Given a project memory entry in "CECW" has status "needs_review"
    And "fabio" has effective project role "reviewer" in project "CECW"
    When "fabio" approves the memory entry with comment "Still valid"
    Then the memory status is "active"

  Scenario: Active memory can be marked needs review
    Given a project memory entry in "CECW" has status "active"
    And "fabio" has effective project role "reviewer" in project "CECW"
    When "fabio" marks the memory entry as needs review
    Then the memory status is "needs_review"
    And an audit event "memory_entry.marked_needs_review" is emitted

  Scenario: Active memory can be deprecated
    Given a project memory entry in "CECW" has status "active"
    And "fabio" has effective project role "reviewer" in project "CECW"
    When "fabio" deprecates the memory entry
    Then the memory status is "deprecated"
    And an audit event "memory_entry.deprecated" is emitted

  Scenario: Deprecated memory can be archived
    Given a project memory entry in "CECW" has status "deprecated"
    And "fabio" has effective project role "maintainer" in project "CECW"
    When "fabio" archives the memory entry
    Then the memory status is "archived"
    And an audit event "memory_entry.archived" is emitted

  Scenario: API does not call LLM during memory creation
    Given "pablo" creates a memory entry submitted by source tool "codex"
    When the API persists the memory entry
    Then no LLM provider is called by the API
    And the source tool is recorded as "codex"
