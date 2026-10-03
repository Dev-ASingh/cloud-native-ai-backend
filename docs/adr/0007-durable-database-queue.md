# ADR 0007: Durable database queue boundary

## Status

Accepted

## Decision

New jobs are persisted with status `queued`. A worker-facing repository
operation claims the oldest queued job and changes it to `running`; explicit
completion changes it to `completed`. Cancellation is allowed only while a job
is queued.

The first worker boundary uses the existing database so queue semantics can be
tested without introducing a broker dependency before the domain transitions
are stable. The repository uses a row-locking query where the configured
database supports it; the production queue adapter and lease/visibility
timeout policy remain follow-up work.

## Consequences

- Accepted work survives API process restarts.
- Idempotency returns the durable queued or already-transitioned job.
- Worker execution is separated from HTTP request handling.
- A database-backed queue is not yet sufficient for production throughput or
  failure recovery; leases, retries, dead-letter handling, and a broker adapter
  are still required.
