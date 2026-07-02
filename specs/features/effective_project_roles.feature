@core @authorization @projects
Feature: Effective project roles
  Project access can come from explicit project membership or from membership in the owning group.
  If multiple roles apply, the highest role wins.

  Background:
    Given organization "acme" exists
    And group "Backend Team" exists in organization "acme"
    And group "AI Team" exists in organization "acme"
    And project "PAY" is owned by group "Backend Team"

  Scenario: Owning group member derives contributor role
    Given user "morgan" is a "member" of group "Backend Team"
    When the system resolves "morgan" effective role in project "PAY"
    Then the effective project role is "contributor"

  Scenario: Owning group lead derives maintainer role
    Given user "riley" is a "lead" of group "Backend Team"
    When the system resolves "riley" effective role in project "PAY"
    Then the effective project role is "maintainer"

  Scenario: Explicit project membership grants access outside owning group
    Given user "dana" is a "member" of group "AI Team"
    And "dana" has explicit project role "reviewer" in project "PAY"
    When the system resolves "dana" effective role in project "PAY"
    Then the effective project role is "reviewer"

  Scenario: Highest project role wins across inherited and explicit roles
    Given user "morgan" is a "member" of group "Backend Team"
    And "morgan" has explicit project role "reviewer" in project "PAY"
    When the system resolves "morgan" effective role in project "PAY"
    Then the effective project role is "reviewer"

  Scenario: Explicit viewer can read project memory but cannot propose it
    Given user "dana" has explicit project role "viewer" in project "PAY"
    When "dana" tries to create project memory in "PAY"
    Then the request is denied
    And an audit event "authorization.denied" is emitted

  Scenario: Parent group does not grant permissions in product
    Given group "Engineering" is the parent of group "Backend Team"
    And user "jordan" is a "lead" of group "Engineering"
    When the system resolves "jordan" effective role in project "PAY"
    Then no effective project role is returned
