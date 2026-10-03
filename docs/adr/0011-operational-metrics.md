# ADR 0011: Operational metrics boundary

## Status

Accepted

## Decision

The API exposes an authenticated operational metrics endpoint. Database-backed
job gauges are filtered by the caller's organization. Worker counters remain
process-local until a centralized metrics backend is introduced.

The first counters cover empty polls, claims, attempts, completions, retries,
failures, and terminal failures. The endpoint returns stable metric names and
integer values rather than raw logs or payloads.

## Consequences

- Queue depth and worker activity can be inspected during local evaluation.
- Metrics are not durable across process restarts and are not suitable for
  alerting until exported to a centralized backend.
- Authentication and organization scoping prevent unauthenticated or
  cross-organization operational disclosure.
