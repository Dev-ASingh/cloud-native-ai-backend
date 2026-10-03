# ADR 0004: Enforce Authorization Through Persisted Memberships

- Status: Accepted
- Date: 2026-10-04

## Context

Milestone 2 persisted jobs and idempotency keys, but the development identity
headers still supplied the organization and role without a database-backed
membership check. That allowed the transport boundary to claim an identity
that the application had never provisioned.

## Decision

Persist users, organizations, and active memberships. The current development
identity adapter may identify a user and organization through headers, but the
application must resolve an active membership from the database and use its
stored role. The role header is ignored for authorization.

## Consequences

- Unknown users and inactive memberships are denied.
- A user cannot claim access to an organization without a membership record.
- Role escalation through request headers is prevented.
- A real identity/session provider is still required before deployment.
- Membership administration and lifecycle auditing are required in a later
  milestone.
