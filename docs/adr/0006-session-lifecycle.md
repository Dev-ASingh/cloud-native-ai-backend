# ADR 0006: Keep Session Issuance Server-Side Until Identity Is Designed

- Status: Accepted
- Date: 2026-10-04

## Context

Adding a login endpoint without account verification, credential recovery,
abuse protection, and identity-provider decisions would create a misleading
security boundary.

## Decision

Implement high-entropy token issuance and revocation as server-side service
operations. Store only token hashes, bind sessions to an organization, enforce
expiry, and expose only authenticated self-revocation. Do not expose an
unauthenticated session-creation endpoint yet.

## Consequences

- The API cannot be used as an accidental open login service.
- Session lifecycle behavior is testable independently of transport.
- Account verification, rotation, recovery, rate limiting, and login audit
  requirements remain explicit follow-up work.
