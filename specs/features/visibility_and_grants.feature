@core @authorization @visibility
Feature: Visibility changes and restricted grants
  Visibility controls audience and must not be expanded without review authority.
  Restricted memory uses explicit user grants.

  Background:
    Given organization "aircury" exists
    And active user "pablo" exists in organization "aircury"
    And active user "fabio" exists in organization "aircury"
    And group "Backend Team" exists in organization "aircury"
    And project "CECW" is owned by group "Backend Team"

  Scenario: Owner adds a viewer grant to restricted memory
    Given "pablo" owns an "active" restricted memory entry
    When "pablo" grants "viewer" access to "fabio"
    Then "fabio" can read the memory entry
    And an audit event "memory_entry.grant_added" is emitted

  Scenario: Removing a grant removes restricted access
    Given "pablo" owns an "active" restricted memory entry
    And "pablo" granted "viewer" access to "fabio"
    When "pablo" removes the grant for "fabio"
    Then "fabio" cannot read the memory entry
    And an audit event "memory_entry.grant_removed" is emitted

  Scenario: Grants do not model group access
    Given "pablo" owns an "active" restricted memory entry
    When "pablo" tries to grant access to group "Backend Team"
    Then the request is rejected
    And no memory entry grant is created

  Scenario: Owner changes private memory to restricted
    Given "pablo" owns an "active" private memory entry
    When "pablo" changes visibility to "restricted"
    Then the visibility scope is "restricted"
    And the memory status remains "active"
    And an audit event "memory_entry.visibility_changed" is emitted

  Scenario: Group member expands private memory to group and requires review
    Given "pablo" owns an "active" private memory entry
    And "pablo" is a "member" of group "Backend Team"
    When "pablo" changes visibility to "group" for group "Backend Team"
    Then the visibility scope is "group"
    And the memory status is "pending_review"
    And the response says review is required

  Scenario: Group lead expands private memory to group as active
    Given "fabio" owns an "active" private memory entry
    And "fabio" is a "lead" of group "Backend Team"
    When "fabio" changes visibility to "group" for group "Backend Team"
    Then the visibility scope is "group"
    And the memory status is "active"

  Scenario: Project contributor expands private memory to project and requires review
    Given "pablo" owns an "active" private memory entry associated to project "CECW"
    And "pablo" has effective project role "contributor" in project "CECW"
    When "pablo" changes visibility to "project" for project "CECW"
    Then the visibility scope is "project"
    And the memory status is "pending_review"

  Scenario: Project reviewer expands private memory to project as active
    Given "fabio" owns an "active" private memory entry associated to project "CECW"
    And "fabio" has effective project role "reviewer" in project "CECW"
    When "fabio" changes visibility to "project" for project "CECW"
    Then the visibility scope is "project"
    And the memory status is "active"

  Scenario: Knowledge admin expands project memory to organization
    Given an "active" project memory entry belongs to project "CECW"
    And "fabio" has organization role "knowledge_admin"
    When "fabio" changes visibility to "organization"
    Then the visibility scope is "organization"
    And the memory status is "active"
    And an audit event "memory_entry.visibility_changed" is emitted

  Scenario: Non knowledge admin cannot expand project memory to organization as active
    Given an "active" project memory entry belongs to project "CECW"
    And "pablo" has organization role "member"
    When "pablo" changes visibility to "organization"
    Then the request is denied or the memory becomes "pending_review"
    And the memory does not become active organization memory without knowledge admin approval

  Scenario: Project visibility requires project id
    Given "pablo" owns an "active" private memory entry
    When "pablo" changes visibility to "project" without a project id
    Then the request is rejected
    And the memory visibility is unchanged

  Scenario: Group visibility requires visibility group id
    Given "pablo" owns an "active" private memory entry
    When "pablo" changes visibility to "group" without a visibility group id
    Then the request is rejected
    And the memory visibility is unchanged
