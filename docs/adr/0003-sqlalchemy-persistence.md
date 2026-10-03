# ADR 0003: Use SQLAlchemy with Alembic for Persistence

- Status: Accepted
- Date: 2026-10-04

## Context

Milestone 1 used an in-memory repository to prove API and domain behavior. The
next gate requires durable job records and idempotency across process restarts
without coupling the domain layer to a specific database vendor.

## Decision

Use SQLAlchemy 2 as the persistence boundary and Alembic for schema changes.
SQLite is the local default for fast development and PostgreSQL is supported
through `DATABASE_URL`. The API depends on a repository adapter rather than
constructing database queries directly.

## Consequences

- Job and idempotency records survive process restarts.
- Schema evolution is reviewable and reversible through migration files.
- PostgreSQL-specific behavior must be tested before production deployment.
- Authentication headers remain a temporary development adapter.
- Runtime initialization currently creates tables for local convenience; a
  deployment environment must run migrations explicitly and disable implicit
  schema creation before release.
