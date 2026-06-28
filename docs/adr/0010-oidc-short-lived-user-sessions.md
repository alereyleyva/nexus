# ADR-0010: OIDC And Short-Lived User Sessions

Status: Accepted
Date: 2026-06-28

## Context

Nexus needs UI and CLI authentication for real users. The CLI should support `nexus login` with SSO, starting with Google and allowing a future organization IdP. Long-lived personal API tokens increase credential leakage risk and create another permission model to manage.

The product still needs AI tools and CLIs to act on behalf of users, but the credential should be temporary, revocable, and tied to an authenticated user session.

## Decision

Use OIDC login with short-lived Nexus-issued session credentials.

Google OIDC is the first provider. The auth implementation must keep provider behavior behind an adapter boundary so a generic OIDC IdP can be added later without changing authorization rules.

The UI and CLI authenticate real users through OIDC. After successful provider login, Nexus issues:

| Credential | Requirement |
| --- | --- |
| Access token | Short-lived Nexus JWT, intended lifetime 5-15 minutes. |
| Refresh token | Opaque random value, stored only as a hash, rotated on every refresh, revocable. |
| Auth session | Server-side session row that records user, organization, provider, client type, capabilities, max visibility, expiry, revocation, and last use. |

The CLI flow uses browser SSO, not static API token creation:

```text
nexus login
-> CLI starts a login authorization with Nexus
-> CLI opens the browser to a Nexus verification URL
-> User signs in with Google or future OIDC IdP
-> Nexus authorizes the pending CLI login
-> CLI exchanges the one-time login code for short-lived session credentials
```

API requests use:

```http
Authorization: Bearer <nexus_access_token>
X-Request-Id: <uuid>
```

An access token identifies an auth session and user. Authorization decisions are still made from current user status, organization membership, group/project roles, memory visibility, memory status, and optional session restrictions. Session capabilities and `max_visibility_scope` restrict permissions; they never expand user permissions.

Personal API tokens are not part of the product v1. Future non-human integrations must use a separate service-account design and ADR.

## Consequences

The CLI gets the desired `nexus login` experience with SSO and no long-lived personal tokens. Compromised access tokens have short lifetimes. Compromised refresh tokens can be revoked by deleting the auth session and are safer because only hashes are stored.

The API must validate Nexus JWT signature, issuer, audience, expiry, and session id. It must also verify the session is not revoked or expired and the user is still active.

Tests should cover login/session validation, refresh rotation, revocation, disabled users, session capability restriction, and max visibility restriction.

## Alternatives Considered

| Alternative | Rejection reason |
| --- | --- |
| Long-lived personal API tokens | Higher leakage risk and less aligned with SSO-first CLI login. |
| CLI stores Google tokens directly | Couples clients to provider details and complicates future IdP support. |
| Source tools as permission actors | Violates human accountability. |
| Service accounts in v1 | Premature for user-driven CLI and UI workflows. |

## Links

| Spec | File |
| --- | --- |
| Authorization | `specs/security/authorization.md` |
| API | `specs/api/rest-api.md` |
| Data model | `specs/data/schema.dbml` |
| Auth feature | `specs/features/auth_and_sessions.feature` |
