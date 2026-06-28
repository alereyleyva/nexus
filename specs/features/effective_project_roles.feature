@core @authorization @projects
Feature: Effective project roles
  Project access can come from explicit project membership or from membership in the owning group.
  If multiple roles apply, the highest role wins.

  Background:
    Given organization "aircury" exists
    And group "Backend Team" exists in organization "aircury"
    And group "AI Team" exists in organization "aircury"
    And project "CECW" is owned by group "Backend Team"

  Scenario: Owning group member derives contributor role
    Given user "pablo" is a "member" of group "Backend Team"
    When the system resolves "pablo" effective role in project "CECW"
    Then the effective project role is "contributor"

  Scenario: Owning group lead derives maintainer role
    Given user "fabio" is a "lead" of group "Backend Team"
    When the system resolves "fabio" effective role in project "CECW"
    Then the effective project role is "maintainer"

  Scenario: Explicit project membership grants access outside owning group
    Given user "carlos" is a "member" of group "AI Team"
    And "carlos" has explicit project role "reviewer" in project "CECW"
    When the system resolves "carlos" effective role in project "CECW"
    Then the effective project role is "reviewer"

  Scenario: Highest project role wins across inherited and explicit roles
    Given user "pablo" is a "member" of group "Backend Team"
    And "pablo" has explicit project role "reviewer" in project "CECW"
    When the system resolves "pablo" effective role in project "CECW"
    Then the effective project role is "reviewer"

  Scenario: Explicit viewer can read project memory but cannot propose it
    Given user "carlos" has explicit project role "viewer" in project "CECW"
    When "carlos" tries to create project memory in "CECW"
    Then the request is denied
    And an audit event "authorization.denied" is emitted

  Scenario: Parent group does not grant permissions in product
    Given group "Engineering" is the parent of group "Backend Team"
    And user "ana" is a "lead" of group "Engineering"
    When the system resolves "ana" effective role in project "CECW"
    Then no effective project role is returned
