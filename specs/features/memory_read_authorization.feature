@core @authorization @memory
Feature: Memory read authorization
  Every read path must enforce organization, status, deletion, and visibility rules.

  Background:
    Given organization "acme" exists
    And organization "other-org" exists
    And group "Backend Team" exists in organization "acme"
    And project "PAY" is owned by group "Backend Team"
    And active user "morgan" exists in organization "acme"
    And active user "riley" exists in organization "acme"

  Scenario: Private memory is readable by owner
    Given "morgan" owns an "active" private memory entry
    When "morgan" requests the memory entry
    Then the request succeeds

  Scenario: Private memory is not readable by another user
    Given "morgan" owns an "active" private memory entry
    When "riley" requests the memory entry
    Then the request is denied
    And an audit event "authorization.denied" is emitted

  Scenario: Organization admin cannot read private memory owned by another user
    Given "morgan" owns an "active" private memory entry
    And "riley" has organization admin capability
    When "riley" requests the memory entry
    Then the request is denied

  Scenario: Restricted memory is readable by explicit grantee
    Given "morgan" owns an "active" restricted memory entry
    And "morgan" granted "viewer" access to "riley"
    When "riley" requests the memory entry
    Then the request succeeds

  Scenario: Restricted memory is not readable without grant
    Given "morgan" owns an "active" restricted memory entry
    When "riley" requests the memory entry
    Then the request is denied

  Scenario: Group memory is readable by group member
    Given "morgan" is a "member" of group "Backend Team"
    And an "active" group memory entry is visible to group "Backend Team"
    When "morgan" requests the memory entry
    Then the request succeeds

  Scenario: Group memory is not readable outside the group
    Given "riley" is not a member of group "Backend Team"
    And an "active" group memory entry is visible to group "Backend Team"
    When "riley" requests the memory entry
    Then the request is denied

  Scenario: Project memory is readable with effective project access
    Given "morgan" is a "member" of group "Backend Team"
    And an "active" project memory entry belongs to project "PAY"
    When "morgan" requests the memory entry
    Then the request succeeds

  Scenario: Project memory is not readable without effective project access
    Given "riley" has no effective role in project "PAY"
    And an "active" project memory entry belongs to project "PAY"
    When "riley" requests the memory entry
    Then the request is denied

  Scenario: Organization memory is readable by active organization member
    Given "morgan" is an active organization member
    And an "active" organization memory entry exists in organization "acme"
    When "morgan" requests the memory entry
    Then the request succeeds

  Scenario: Disabled organization user cannot read organization memory
    Given "morgan" is disabled
    And an "active" organization memory entry exists in organization "acme"
    When "morgan" requests the memory entry
    Then the request is denied

  Scenario: Project association does not imply project visibility
    Given "morgan" owns an "active" private memory entry associated to project "PAY"
    And "riley" has effective project role "maintainer" in project "PAY"
    When "riley" requests the memory entry
    Then the request is denied

  Scenario: Cross-organization reads are denied
    Given "morgan" is active in organization "acme"
    And an "active" organization memory entry exists in organization "other-org"
    When "morgan" requests the memory entry
    Then the request is denied

  Scenario Outline: Normal reads hide non-default statuses
    Given "morgan" owns a "<status>" private memory entry
    When "morgan" requests the memory entry through a normal read path
    Then the memory entry is not returned

    Examples:
      | status         |
      | pending_review |
      | rejected       |
      | deprecated     |
      | archived       |

  Scenario: Needs review memory is readable with warning metadata
    Given "morgan" owns a "needs_review" private memory entry
    When "morgan" requests the memory entry through a normal read path
    Then the memory entry is returned
    And the response marks the memory as needing review
