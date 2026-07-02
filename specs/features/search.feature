@core @search @authorization
Feature: Authorized memory search
  Search uses PostgreSQL full text search over memory the actor is allowed to read.

  Background:
    Given organization "acme" exists
    And active user "morgan" exists in organization "acme"
    And active user "riley" exists in organization "acme"
    And group "Backend Team" exists in organization "acme"
    And project "PAY" is owned by group "Backend Team"

  Scenario: Search finds authorized memory by title
    Given "morgan" can read an active memory titled "Payment sync retries must use idempotency keys"
    When "morgan" searches for "idempotency keys"
    Then the memory entry is returned

  Scenario: Search finds authorized memory by body
    Given "morgan" can read an active memory with body "Concurrent retries can duplicate payment events"
    When "morgan" searches for "duplicate payment events"
    Then the memory entry is returned

  Scenario: Search finds authorized memory by rationale
    Given "morgan" can read an active memory with rationale "The retry path can execute twice"
    When "morgan" searches for "retry path execute twice"
    Then the memory entry is returned

  Scenario: Search finds authorized memory by tags
    Given "morgan" can read an active memory tagged "payments" and "sync"
    When "morgan" searches with tag filter "payments"
    Then the memory entry is returned

  Scenario: Search does not return unauthorized project memory
    Given "riley" has no effective role in project "PAY"
    And an active project memory entry belongs to project "PAY"
    When "riley" searches for text that matches the project memory entry
    Then the search results are empty
    And direct GET for the memory entry would be denied

  Scenario: Search does not return private memory owned by another user
    Given "morgan" owns an active private memory entry matching "payments"
    When "riley" searches for "payments"
    Then the search results do not include the memory entry

  Scenario: Search filters by project without bypassing visibility
    Given "morgan" owns an active private memory entry associated to project "PAY" matching "payments"
    And "riley" has effective project role "maintainer" in project "PAY"
    When "riley" searches in project "PAY" for "payments"
    Then the search results do not include "morgan" private memory entry

  Scenario: Search filters by memory type
    Given "morgan" can read an active "decision" memory matching "payments"
    And "morgan" can read an active "note" memory matching "payments"
    When "morgan" searches for "payments" with type filter "decision"
    Then only the "decision" memory is returned

  Scenario Outline: Search excludes hidden statuses by default
    Given "morgan" can otherwise read a "<status>" memory matching "payments"
    When "morgan" searches for "payments" with default status settings
    Then the memory entry is not returned

    Examples:
      | status         |
      | pending_review |
      | rejected       |
      | deprecated     |
      | archived       |

  Scenario: Search returns needs review memory with warning marker
    Given "morgan" can read a "needs_review" memory matching "payments"
    When "morgan" searches for "payments"
    Then the memory entry is returned
    And the result marks the memory as needing review

  Scenario: Search can include deprecated only when explicitly requested and authorized
    Given "morgan" can read a "deprecated" memory matching "payments"
    When "morgan" searches for "payments" and explicitly includes status "deprecated"
    Then the memory entry is returned

  Scenario: Search emits audit without raw query by default
    Given "morgan" can search memory
    When "morgan" searches for "payment sync retries idempotency"
    Then an audit event "search.executed" is emitted
    And the audit metadata includes a query hash
    And the audit metadata does not include the raw query
