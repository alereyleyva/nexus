@core @authorization @memory
Feature: Memory read authorization
  Every read path must enforce organization, status, deletion, and visibility rules.

  Background:
    Given organization "aircury" exists
    And organization "other-org" exists
    And group "Backend Team" exists in organization "aircury"
    And project "CECW" is owned by group "Backend Team"
    And active user "pablo" exists in organization "aircury"
    And active user "fabio" exists in organization "aircury"

  Scenario: Private memory is readable by owner
    Given "pablo" owns an "active" private memory entry
    When "pablo" requests the memory entry
    Then the request succeeds

  Scenario: Private memory is not readable by another user
    Given "pablo" owns an "active" private memory entry
    When "fabio" requests the memory entry
    Then the request is denied
    And an audit event "authorization.denied" is emitted

  Scenario: Organization admin cannot read private memory owned by another user
    Given "pablo" owns an "active" private memory entry
    And "fabio" has organization admin capability
    When "fabio" requests the memory entry
    Then the request is denied

  Scenario: Restricted memory is readable by explicit grantee
    Given "pablo" owns an "active" restricted memory entry
    And "pablo" granted "viewer" access to "fabio"
    When "fabio" requests the memory entry
    Then the request succeeds

  Scenario: Restricted memory is not readable without grant
    Given "pablo" owns an "active" restricted memory entry
    When "fabio" requests the memory entry
    Then the request is denied

  Scenario: Group memory is readable by group member
    Given "pablo" is a "member" of group "Backend Team"
    And an "active" group memory entry is visible to group "Backend Team"
    When "pablo" requests the memory entry
    Then the request succeeds

  Scenario: Group memory is not readable outside the group
    Given "fabio" is not a member of group "Backend Team"
    And an "active" group memory entry is visible to group "Backend Team"
    When "fabio" requests the memory entry
    Then the request is denied

  Scenario: Project memory is readable with effective project access
    Given "pablo" is a "member" of group "Backend Team"
    And an "active" project memory entry belongs to project "CECW"
    When "pablo" requests the memory entry
    Then the request succeeds

  Scenario: Project memory is not readable without effective project access
    Given "fabio" has no effective role in project "CECW"
    And an "active" project memory entry belongs to project "CECW"
    When "fabio" requests the memory entry
    Then the request is denied

  Scenario: Organization memory is readable by active organization member
    Given "pablo" is an active organization member
    And an "active" organization memory entry exists in organization "aircury"
    When "pablo" requests the memory entry
    Then the request succeeds

  Scenario: Disabled organization user cannot read organization memory
    Given "pablo" is disabled
    And an "active" organization memory entry exists in organization "aircury"
    When "pablo" requests the memory entry
    Then the request is denied

  Scenario: Project association does not imply project visibility
    Given "pablo" owns an "active" private memory entry associated to project "CECW"
    And "fabio" has effective project role "maintainer" in project "CECW"
    When "fabio" requests the memory entry
    Then the request is denied

  Scenario: Cross-organization reads are denied
    Given "pablo" is active in organization "aircury"
    And an "active" organization memory entry exists in organization "other-org"
    When "pablo" requests the memory entry
    Then the request is denied

  Scenario Outline: Normal reads hide non-default statuses
    Given "pablo" owns a "<status>" private memory entry
    When "pablo" requests the memory entry through a normal read path
    Then the memory entry is not returned

    Examples:
      | status         |
      | pending_review |
      | rejected       |
      | deprecated     |
      | archived       |

  Scenario: Needs review memory is readable with warning metadata
    Given "pablo" owns a "needs_review" private memory entry
    When "pablo" requests the memory entry through a normal read path
    Then the memory entry is returned
    And the response marks the memory as needing review
