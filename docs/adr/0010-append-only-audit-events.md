# ADR 0010: Append-only audit events

## Status

Accepted

## Decision

Worker completion and failure write append-only, organization-scoped audit
events. Each event records an actor, action, target, outcome, timestamp, and
small transition metadata such as the attempt number. Payloads, bearer tokens,
credentials, and provider output are excluded.

The initial implementation persists events in the same database and exposes
only an insert-oriented writer. No update or delete API is provided to
application code.

## Consequences

- Job outcomes can be inspected without reconstructing logs.
- Audit data follows organization boundaries and remains queryable after
  process restarts.
- Retention, tamper-evident export, event search APIs, and centralized
  telemetry remain future operational work.
