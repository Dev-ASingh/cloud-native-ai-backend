# ADR 0009: Worker process boundary

## Status

Accepted

## Decision

Worker execution is represented by a small process-facing `Worker` boundary.
It claims one leased job, invokes a narrow executor protocol, and records
completion or failure through the repository. The initial executor is
deterministic and intentionally does not call an external model or provider.

The worker does not log payloads or credentials. Execution exceptions are
logged with the job identifier only and are converted into the repository's
bounded retry transition.

## Consequences

- HTTP requests never execute job work inline.
- Provider adapters can be added behind `JobExecutor` without changing claim
  or state-transition logic.
- The current module supports one-shot execution evidence; a long-running
  supervisor, broker transport, graceful shutdown, and metrics remain future
  work.
