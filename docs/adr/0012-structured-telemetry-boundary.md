# ADR 0012: Structured telemetry boundary

## Status

Accepted

## Decision

HTTP request completion is emitted as a JSON log record with method, path,
duration, and request ID. The request ID is carried through a context variable
so application logs can correlate work without passing transport objects
through domain code.

Metrics expose a narrow exporter protocol. The current implementation keeps
worker counters process-local and provides an in-memory exporter for tests;
centralized metrics and tracing adapters can be introduced without changing
the worker or API contracts.

Request bodies, authorization headers, credentials, and provider output are
never included in the request log record.

## Consequences

- Local logs are machine-readable and correlate API activity.
- Exporter integration is explicit rather than coupled to a vendor SDK.
- Logs and counters remain local until deployment-specific aggregation is
  configured.
