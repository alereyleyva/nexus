@core @context-packs @authorization
Feature: Authorized context packs
  Context packs select and group authorized memory for a task.
  They are not persisted and do not call LLMs.

  Background:
    Given organization "aircury" exists
    And active user "fabio" exists in organization "aircury"
    And project "CECW" exists in organization "aircury"

  Scenario: Context pack groups authorized memory by type
    Given "fabio" can read an active "decision" memory in project "CECW"
    And "fabio" can read an active "problem" memory in project "CECW"
    And "fabio" can read an active "solution" memory in project "CECW"
    When "fabio" generates a context pack for project "CECW"
    Then the decision memory appears under "decisions"
    And the problem memory appears under "problems"
    And the solution memory appears under "solutions"

  Scenario: Context pack respects max items
    Given "fabio" can read 30 active memories in project "CECW"
    When "fabio" generates a context pack with max items 20
    Then the context pack contains at most 20 items

  Scenario: Context pack excludes unauthorized memory
    Given "fabio" cannot read a private memory matching the task
    When "fabio" generates a context pack for the task
    Then the private memory is not included

  Scenario Outline: Context pack excludes hidden statuses by default
    Given "fabio" can otherwise read a "<status>" memory matching the task
    When "fabio" generates a normal context pack
    Then the memory entry is not included

    Examples:
      | status         |
      | pending_review |
      | rejected       |
      | deprecated     |
      | archived       |

  Scenario: Context pack includes needs review warning
    Given "fabio" can read a "needs_review" memory matching the task
    When "fabio" generates a context pack
    Then the memory entry is included
    And the context pack warnings include type "needs_review"

  Scenario: Context pack project filter does not bypass visibility
    Given "pablo" owns a private memory associated to project "CECW" matching the task
    And "fabio" has effective project role "maintainer" in project "CECW"
    When "fabio" generates a context pack for project "CECW"
    Then "pablo" private memory is not included

  Scenario: Context pack generation is audited
    Given "fabio" can generate context packs
    When "fabio" generates a context pack for project "CECW"
    Then an audit event "context_pack.generated" is emitted

  Scenario: API does not summarize context packs with an LLM
    Given "fabio" generates a context pack for project "CECW"
    When the API returns the context pack
    Then the response is structured JSON
    And no LLM provider is called by the API
    And no memory entry is created by the context pack operation
