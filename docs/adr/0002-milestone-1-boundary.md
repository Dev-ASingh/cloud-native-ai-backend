# ADR 0002: Use Replaceable Development Adapters for Milestone 1

- Status: Accepted
- Date: 2026-10-04

## Context

The first implementation must prove request validation, organization
authorization, idempotency, state transitions, error behavior, and health
signals before infrastructure choices obscure the domain contract.

## Decision

Milestone 1 uses:

- In-memory job persistence.
- Explicit development identity headers.
- Synchronous job acceptance and cancellation.
- Deterministic API behavior with no model provider.

These boundaries must be represented as replaceable interfaces and clearly
marked as non-production.

## Superseded persistence boundary

Milestone 2 replaces the in-memory job repository with SQLAlchemy persistence
and an Alembic-managed schema. The development identity headers remain
temporary.

## Consequences

- The API and domain behavior can be tested without external services.
- No production durability or authentication claim is implied.
- Milestone 2 must replace persistence and identity before deployment.
- The repository remains private until the publication gates are satisfied.
