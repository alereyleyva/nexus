@core @auth
Feature: Authentication and short-lived user sessions
  The API authenticates real users through Google OIDC-backed Nexus sessions.
  CLI credentials are short-lived, refreshable, revocable, and never become independent actors.

  Background:
    Given organization "aircury" exists
    And user "pablo" is active in organization "aircury"
    And user "fabio" is active in organization "aircury"

  Scenario: OIDC login resolves an actor context
    Given "pablo" completes Google OIDC login
    When the API authenticates the Nexus access token
    Then the actor context user is "pablo"
    And the actor context organization is "aircury"
    And the actor context session id is present

  Scenario: CLI login uses browser SSO
    Given "pablo" runs "nexus login"
    When the CLI opens the browser verification URL
    And "pablo" completes Google OIDC login
    Then the CLI receives a Nexus access token
    And the CLI receives a refresh token
    And an audit event "auth.session.created" is emitted

  Scenario: Signed-in user approves a pending CLI login
    Given "pablo" runs "nexus login"
    And "pablo" is signed in on the web client
    When "pablo" approves the pending CLI login for its user code
    Then the pending CLI login is bound to "pablo" in organization "aircury"
    And the pending CLI login status becomes "approved"
    And the CLI can exchange its device code for Nexus credentials

  Scenario: Signed-in user denies a pending CLI login
    Given "pablo" runs "nexus login"
    And "pablo" is signed in on the web client
    When "pablo" denies the pending CLI login for its user code
    Then the pending CLI login status becomes "denied"
    And the CLI device code exchange is rejected

  Scenario: CLI token polling waits for browser approval
    Given "pablo" runs "nexus login"
    And the browser verification has not completed
    When the CLI polls "POST /v1/auth/cli/token"
    Then the API returns status "authorization_pending"

  Scenario: CLI device code cannot be exchanged twice
    Given "pablo" completed "nexus login" and exchanged the CLI device code
    When the CLI exchanges the same device code again
    Then the request is rejected with conflict
    And no additional auth session is created

  Scenario: Disabled users cannot authenticate
    Given user "pablo" is disabled
    And "pablo" has an unexpired Nexus access token
    When the API authenticates the request
    Then the request is denied
    And an audit event "authorization.denied" is emitted

  Scenario Outline: Invalid session lifecycle denies authentication
    Given "pablo" has a Nexus auth session
    And the session is <state>
    When the API authenticates the session access token
    Then the request is denied
    And an audit event "authorization.denied" is emitted

    Examples:
      | state   |
      | expired |
      | revoked |

  Scenario: Refresh token rotation issues new credentials
    Given "pablo" has an active CLI auth session
    And the refresh token has not been used
    When the CLI refreshes the session
    Then a new access token is issued
    And a new refresh token is issued
    And the old refresh token is marked used
    And an audit event "auth.session.refreshed" is emitted

  Scenario: Refresh token reuse revokes the session
    Given "pablo" has an active CLI auth session
    And a previous refresh token was already used
    When the previous refresh token is used again
    Then the session is revoked
    And an audit event "auth.refresh_reuse_detected" is emitted

  Scenario: Session capability is required for restricted sessions
    Given "pablo" has a restricted CLI session with capability "memory:read"
    When "pablo" calls "POST /v1/memory-entries" with that session
    Then the request is denied
    And the denial reason mentions missing capability "memory:create"
    And an audit event "authorization.denied" is emitted

  Scenario: Session cannot create above max visibility scope
    Given "pablo" has organization role "knowledge_admin"
    And "pablo" has a CLI session with capability "memory:create"
    And the session max visibility scope is "project"
    When "pablo" uses the session to create "organization" memory
    Then the request is denied
    And no memory entry is created
    And an audit event "authorization.denied" is emitted

  Scenario: Session cannot expand user review permissions
    Given "pablo" has effective project role "contributor" in project "CECW"
    And "pablo" has a CLI session with capability "memory:review"
    And a project memory entry in "CECW" is pending review
    When "pablo" uses the session to approve the memory entry
    Then the request is denied
    And the memory entry remains "pending_review"
    And an audit event "authorization.denied" is emitted

  Scenario: The API does not need X-On-Behalf-Of in product
    Given "pablo" has an active CLI auth session
    When the API authenticates the session without "X-On-Behalf-Of"
    Then the actor context user is resolved from the session user
    And the request does not require an on-behalf-of header
