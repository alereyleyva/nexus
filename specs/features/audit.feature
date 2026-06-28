@core @audit @security
Feature: Audit events
  Sensitive operations and denials are audited with safe metadata.

  Background:
    Given organization "aircury" exists
    And active user "pablo" exists in organization "aircury"

  Scenario Outline: Memory operations emit audit events
    Given "pablo" is authorized for operation "<operation>"
    When "pablo" performs operation "<operation>"
    Then an audit event "<event>" is emitted
    And the audit event includes organization id
    And the audit event includes actor user id
    And the audit event includes request id

    Examples:
      | operation         | event                            |
      | create memory     | memory_entry.created             |
      | update memory     | memory_entry.updated             |
      | approve memory    | memory_entry.approved            |
      | reject memory     | memory_entry.rejected            |
      | change visibility | memory_entry.visibility_changed  |
      | add grant         | memory_entry.grant_added         |
      | remove grant      | memory_entry.grant_removed       |
      | mark needs review | memory_entry.marked_needs_review |
      | deprecate memory  | memory_entry.deprecated          |
      | archive memory    | memory_entry.archived            |

  Scenario: Authorization denial emits audit event
    Given "pablo" is not authorized to read a memory entry
    When "pablo" requests the memory entry
    Then the request is denied
    And an audit event "authorization.denied" is emitted
    And the audit decision is "deny"

  Scenario: Token lifecycle emits audit events
    Given "pablo" creates a personal API token
    Then an audit event "token.created" is emitted
    When "pablo" revokes the personal API token
    Then an audit event "token.revoked" is emitted

  Scenario: Audit event records token id when token is used
    Given "pablo" has an active API token
    When "pablo" creates memory using the API token
    Then an audit event "memory_entry.created" is emitted
    And the audit event actor token id is present

  Scenario: Audit metadata must not store raw token values
    Given "pablo" authenticates with a personal API token
    When an audit event is emitted for the request
    Then the audit metadata does not contain the raw token

  Scenario: Search audit stores hash instead of raw query by default
    Given "pablo" searches for "secret customer payment issue"
    When the search audit event is emitted
    Then the audit metadata contains "query_hash"
    And the audit metadata does not contain "secret customer payment issue"

  Scenario: Context pack generation emits audit event
    Given "pablo" generates a context pack
    Then an audit event "context_pack.generated" is emitted

  Scenario: Audit event has safe resource fields
    Given "pablo" updates a memory entry
    When the audit event is emitted
    Then the audit event resource type is "memory_entry"
    And the audit event resource id is the memory entry id
    And the audit metadata excludes full request body by default
