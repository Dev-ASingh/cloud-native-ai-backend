# ADR 0005: Use Opaque Hashed Session Tokens at the API Boundary

- Status: Accepted
- Date: 2026-10-04

## Context

Trusting user, organization, or role headers is not an acceptable
authentication boundary. The API needs a revocable, expiring credential while
the eventual identity provider is still being selected.

## Decision

Authenticated requests use `Authorization: Bearer <token>`. The service stores
only a SHA-256 token hash, checks revocation and expiry, and then resolves the
user's active organization membership. Token issuance and revocation remain
outside the request-serving API until the identity provider and account
recovery model are designed.

## Consequences

- Raw session tokens are never persisted.
- Expired and revoked sessions are rejected.
- Organization and role cannot be selected by the caller.
- Tests can seed sessions without creating an unsafe login shortcut.
- A production identity provider, secure issuance flow, rotation policy, and
  CSRF/session transport decision are still required.
