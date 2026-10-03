# Threat Model

## Assets

- User identity and session material.
- Organization membership and authorization state.
- Job payloads and generated artifacts.
- Provider credentials and infrastructure secrets.
- Audit events and operational telemetry.
- Database and object-storage integrity.

## Trust boundaries

1. Untrusted HTTP client to API service.
2. API service to database and queue.
3. Queue to worker.
4. Worker to provider adapter.
5. Application to artifact storage.
6. CI system to deployment environment.

## Abuse cases and controls

| Abuse case | Required control |
| --- | --- |
| Cross-organization object access | Server-side membership check on every scoped read and write. |
| Replay of a job request | Required idempotency key with scope, expiry, and original-result replay. |
| Oversized or malformed payload | Schema validation, body limits, and bounded field sizes. |
| Queue message duplication | Idempotent worker execution and state-transition constraints. |
| Provider timeout or malformed output | Timeout, schema validation, bounded retry, and failure state. |
| Secret leakage in logs | Structured redaction tests and prohibited-field policy. |
| Unauthorized delivery | Explicit approval state and server-side policy enforcement. |
| Artifact exposure | Organization-scoped access, signed access path, and retention policy. |
| Dependency compromise | Locked dependencies, automated scanning, and review gates. |
| Deployment credential abuse | Least-privilege short-lived CI credentials and protected environments. |

## Security invariants

- Deny by default.
- Never trust client-supplied organization context.
- Never execute generated code or shell commands.
- Never log credentials, tokens, or full sensitive payloads.
- Never place secrets in the browser bundle or repository.
- Fail closed when authorization or required dependency state is unknown.
- Audit records are append-only and contain identifiers and bounded transition
  metadata, never credentials, tokens, or full job payloads.
- Operational metrics require authentication and scope database-backed job
  gauges to the caller's organization.

## Verification

Security tests must cover broken object-level authorization, idempotency
replay, payload limits, log redaction, malformed provider output, dependency
scanning, and container scanning before public release.
