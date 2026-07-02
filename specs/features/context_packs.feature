@core @context-packs @authorization
Feature: Authorized context packs
  Context packs select and group authorized memory for a task.
  They are not persisted and do not call LLMs.

  Background:
    Given organization "acme" exists
    And active user "riley" exists in organization "acme"
    And project "PAY" exists in organization "acme"

  Scenario: Context pack groups authorized memory by type
    Given "riley" can read an active "decision" memory in project "PAY"
    And "riley" can read an active "problem" memory in project "PAY"
    And "riley" can read an active "solution" memory in project "PAY"
    When "riley" generates a context pack for project "PAY"
    Then the decision memory appears under "decisions"
    And the problem memory appears under "problems"
    And the solution memory appears under "solutions"

  Scenario: Context pack respects max items
    Given "riley" can read 30 active memories in project "PAY"
    When "riley" generates a context pack with max items 20
    Then the context pack contains at most 20 items

  Scenario: Context pack excludes unauthorized memory
    Given "riley" cannot read a private memory matching the task
    When "riley" generates a context pack for the task
    Then the private memory is not included

  Scenario Outline: Context pack excludes hidden statuses by default
    Given "riley" can otherwise read a "<status>" memory matching the task
    When "riley" generates a normal context pack
    Then the memory entry is not included

    Examples:
      | status         |
      | pending_review |
      | rejected       |
      | deprecated     |
      | archived       |

  Scenario: Context pack includes needs review warning
    Given "riley" can read a "needs_review" memory matching the task
    When "riley" generates a context pack
    Then the memory entry is included
    And the context pack warnings include type "needs_review"

  Scenario: Context pack project filter does not bypass visibility
    Given "morgan" owns a private memory associated to project "PAY" matching the task
    And "riley" has effective project role "maintainer" in project "PAY"
    When "riley" generates a context pack for project "PAY"
    Then "morgan" private memory is not included

  Scenario: Context pack generation is audited
    Given "riley" can generate context packs
    When "riley" generates a context pack for project "PAY"
    Then an audit event "context_pack.generated" is emitted

  Scenario: API does not summarize context packs with an LLM
    Given "riley" generates a context pack for project "PAY"
    When the API returns the context pack
    Then the response is structured JSON
    And no LLM provider is called by the API
    And no memory entry is created by the context pack operation
