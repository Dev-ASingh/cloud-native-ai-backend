# Test Strategy

## Test pyramid

### Unit tests

Fast tests cover domain state transitions, authorization policies, validation,
retry classification, idempotency, redaction, and audit-event construction.

### Integration tests

Run against disposable PostgreSQL and Redis services. Cover migrations,
transactions, queue-worker execution, artifact persistence, approval flow, and
dependency failures.

Milestone 2 currently exercises the repository through a local SQLite database
and separately verifies a fresh Alembic upgrade. PostgreSQL integration tests
are required before deployment.

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
