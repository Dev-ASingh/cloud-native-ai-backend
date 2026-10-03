# ADR 0008: Worker leases and bounded retries

## Status

Accepted

## Decision

Each running job records a worker lease owner, lease expiry, and attempt count.
Claiming a queued job increments its attempt count and grants a short lease.
An expired lease is cleared and the job is requeued unless the maximum attempt
count has been reached; terminal failure is then recorded as `failed`.

Completion and failure require the current lease owner. This prevents a stale
worker from completing or requeueing work after another worker has recovered
the lease.

## Consequences

- Worker crashes no longer leave jobs permanently running.
- Retry behavior is bounded and observable through the job attempt count.
- The current database queue remains suitable for deterministic development
  evidence, but production needs a broker-backed visibility timeout and
  operational metrics.
