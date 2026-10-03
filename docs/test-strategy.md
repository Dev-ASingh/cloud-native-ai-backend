# Test Strategy

## Test pyramid

### Unit tests

Fast tests cover domain state transitions, authorization policies, validation,
retry classification, idempotency, redaction, and audit-event construction.

### Integration tests

Run against disposable PostgreSQL and Redis services. Cover migrations,
transactions, queue-worker execution, artifact persistence, approval flow, and
dependency failures.

The local suite exercises the repository, one-shot worker, and audit writer.
CI applies a fresh Alembic upgrade against PostgreSQL before running the same
suite, so migration and runtime behavior are both exercised. The metrics
contract also verifies authentication and organization scoping so one
organization cannot observe another organization's queue depth.
Telemetry tests verify request correlation in structured log records and
snapshot export without including request payloads or credentials.

The CI database path uses PostgreSQL rather than relying only on SQLite
`create_all` behavior.

### Contract tests

Validate the generated OpenAPI contract, stable error envelopes, authentication
requirements, pagination, and cross-organization access rejection.

### Failure tests

Prove behavior when a worker crashes, a queue message is duplicated, a provider
times out, the database is unavailable, artifact storage fails, and an approval
expires.

### Security tests

Cover broken object-level authorization, idempotency replay, oversized
payloads, secret leakage in logs, malformed provider output, dependency
vulnerabilities, and container vulnerabilities.

## Evidence requirements

Each test suite must state:

- What behavior it proves.
- Which threat or reliability requirement it covers.
- Whether it runs locally or in CI.
- What failure output means.

No benchmark or reliability claim belongs in the README until the command,
environment, dataset, and result are recorded.
