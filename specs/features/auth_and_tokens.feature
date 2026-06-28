@core @auth
Feature: Authentication and personal API tokens
  The API authenticates real users and personal tokens.
  Tokens act on behalf of users and restrict permissions.

  Background:
    Given organization "aircury" exists
    And user "pablo" is active in organization "aircury"
    And user "fabio" is active in organization "aircury"

  Scenario: User JWT resolves an actor context
    Given "pablo" has a valid user JWT
    When the API authenticates the request
    Then the actor context user is "pablo"
    And the actor context organization is "aircury"
    And the actor context token id is empty

  Scenario: Disabled users cannot authenticate
    Given user "pablo" is disabled
    And "pablo" has a valid user JWT
    When the API authenticates the request
    Then the request is denied
    And an audit event "authorization.denied" is emitted

  Scenario: Personal API token resolves user and token context
    Given "pablo" has an active API token named "Pablo Codex CLI"
    And the token scopes are "memory:create", "memory:read", "search:read"
    When the API authenticates the token
    Then the actor context user is "pablo"
    And the actor context token id is present
    And the token last used timestamp is updated

  Scenario Outline: Invalid API token lifecycle denies authentication
    Given "pablo" has an API token named "Pablo Codex CLI"
    And the token is <state>
    When the API authenticates the token
    Then the request is denied
    And an audit event "authorization.denied" is emitted

    Examples:
      | state   |
      | expired |
      | revoked |

  Scenario: Token scope is required for endpoint capability
    Given "pablo" has an active API token with scope "memory:read"
    When "pablo" calls "POST /v1/memory-entries" with the token
    Then the request is denied
    And the denial reason mentions missing scope "memory:create"
    And an audit event "authorization.denied" is emitted

  Scenario: Token cannot create above max visibility scope
    Given "pablo" has organization role "knowledge_admin"
    And "pablo" has an active API token with scope "memory:create"
    And the token max visibility scope is "project"
    When "pablo" uses the token to create "organization" memory
    Then the request is denied
    And no memory entry is created
    And an audit event "authorization.denied" is emitted

  Scenario: Token cannot expand user review permissions
    Given "pablo" has effective project role "contributor" in project "CECW"
    And "pablo" has an active API token with scope "memory:review"
    And a project memory entry in "CECW" is pending review
    When "pablo" uses the token to approve the memory entry
    Then the request is denied
    And the memory entry remains "pending_review"
    And an audit event "authorization.denied" is emitted

  Scenario: The API does not need X-On-Behalf-Of in product
    Given "pablo" has an active API token
    When the API authenticates the token without "X-On-Behalf-Of"
    Then the actor context user is resolved from the token owner
    And the request does not require an on-behalf-of header
