@core @search @authorization
Feature: Authorized memory search
  Search uses PostgreSQL full text search over memory the actor is allowed to read.

  Background:
    Given organization "aircury" exists
    And active user "pablo" exists in organization "aircury"
    And active user "fabio" exists in organization "aircury"
    And group "Backend Team" exists in organization "aircury"
    And project "CECW" is owned by group "Backend Team"

  Scenario: Search finds authorized memory by title
    Given "pablo" can read an active memory titled "Payment sync retries must use idempotency keys"
    When "pablo" searches for "idempotency keys"
    Then the memory entry is returned

  Scenario: Search finds authorized memory by body
    Given "pablo" can read an active memory with body "Concurrent retries can duplicate payment events"
    When "pablo" searches for "duplicate payment events"
    Then the memory entry is returned

  Scenario: Search finds authorized memory by rationale
    Given "pablo" can read an active memory with rationale "The retry path can execute twice"
    When "pablo" searches for "retry path execute twice"
    Then the memory entry is returned

  Scenario: Search finds authorized memory by tags
    Given "pablo" can read an active memory tagged "payments" and "sync"
    When "pablo" searches with tag filter "payments"
    Then the memory entry is returned

  Scenario: Search does not return unauthorized project memory
    Given "fabio" has no effective role in project "CECW"
    And an active project memory entry belongs to project "CECW"
    When "fabio" searches for text that matches the project memory entry
    Then the search results are empty
    And direct GET for the memory entry would be denied

  Scenario: Search does not return private memory owned by another user
    Given "pablo" owns an active private memory entry matching "payments"
    When "fabio" searches for "payments"
    Then the search results do not include the memory entry

  Scenario: Search filters by project without bypassing visibility
    Given "pablo" owns an active private memory entry associated to project "CECW" matching "payments"
    And "fabio" has effective project role "maintainer" in project "CECW"
    When "fabio" searches in project "CECW" for "payments"
    Then the search results do not include "pablo" private memory entry

  Scenario: Search filters by memory type
    Given "pablo" can read an active "decision" memory matching "payments"
    And "pablo" can read an active "note" memory matching "payments"
    When "pablo" searches for "payments" with type filter "decision"
    Then only the "decision" memory is returned

  Scenario Outline: Search excludes hidden statuses by default
    Given "pablo" can otherwise read a "<status>" memory matching "payments"
    When "pablo" searches for "payments" with default status settings
    Then the memory entry is not returned

    Examples:
      | status         |
      | pending_review |
      | rejected       |
      | deprecated     |
      | archived       |

  Scenario: Search returns needs review memory with warning marker
    Given "pablo" can read a "needs_review" memory matching "payments"
    When "pablo" searches for "payments"
    Then the memory entry is returned
    And the result marks the memory as needing review

  Scenario: Search can include deprecated only when explicitly requested and authorized
    Given "pablo" can read a "deprecated" memory matching "payments"
    When "pablo" searches for "payments" and explicitly includes status "deprecated"
    Then the memory entry is returned

  Scenario: Search emits audit without raw query by default
    Given "pablo" can search memory
    When "pablo" searches for "payment sync retries idempotency"
    Then an audit event "search.executed" is emitted
    And the audit metadata includes a query hash
    And the audit metadata does not include the raw query
