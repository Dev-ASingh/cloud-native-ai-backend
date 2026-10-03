# ADR 0013: Keep SQLite Development and PostgreSQL Deployment Paths Explicit

- Status: Accepted
- Date: 2026-10-04

## Context

SQLite keeps the first-run developer experience fast, but it does not exercise
the transaction, locking, and connection behavior required by a deployed
multi-process service. PostgreSQL must therefore be a supported runtime path,
not only a planned dependency.

## Decision

The application will support SQLite for isolated local development and
PostgreSQL through `postgresql+psycopg`. Engine setup will apply SQLite-specific
connection arguments only to SQLite URLs and will enable connection health
checks for both paths. PostgreSQL development will be reproducible through the
repository Compose file and Alembic migrations.

## Consequences

- Fast local smoke tests remain available without a database service.
- PostgreSQL integration environments use the same migration path as deployment.
- Queue, transaction, and concurrency behavior still require dedicated
  integration tests before production release.
