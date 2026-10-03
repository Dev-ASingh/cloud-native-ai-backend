# API Contract

## Contract rules

- Base path: `/api/v1`.
- JSON request and response bodies use UTF-8.
- Unknown request fields are rejected unless explicitly documented.
- Mutating requests require authentication and authorization.
- Mutating requests that can be retried require an `Idempotency-Key`.
- Errors use a stable envelope and do not expose stack traces.

## Error envelope

```json
{
  "error": {
    "code": "job_not_found",
    "message": "The requested job was not found.",
    "request_id": "req_01..."
  }
}
```

`message` is safe for the caller. Detailed diagnostics stay in protected
server logs and telemetry.

## Initial endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/session` | Establish a short-lived authenticated session. |
| `POST` | `/auth/session/revoke` | Revoke the current authenticated session. |
| `GET` | `/me` | Return the authenticated principal and memberships. |
| `POST` | `/jobs` | Validate and enqueue a job. |
| `GET` | `/jobs` | List jobs visible to the caller with pagination. |
| `GET` | `/jobs/{job_id}` | Read one authorized job and current state. |
| `POST` | `/jobs/{job_id}/cancel` | Request cooperative cancellation. |
| `POST` | `/jobs/{job_id}/approve` | Approve a job that reached review. |
| `GET` | `/jobs/{job_id}/artifacts` | List authorized job artifacts. |
| `GET` | `/health` | Process liveness. |
| `GET` | `/ready` | Dependency readiness; returns `503` when the database cannot answer a probe query. |

## Session authentication

Authenticated endpoints require an opaque bearer token:

```text
Authorization: Bearer <session-token>
```

Only a SHA-256 hash of the token is stored. The session must be active and
unexpired. The authenticated user is then resolved against an active persisted
organization membership, and the stored membership role is returned. Token
issuance is a server-side service operation until account verification and
recovery exist. The authenticated revoke endpoint invalidates only the current
bearer token.

Sessions are bound to one organization. Legacy session records without an
organization binding are rejected rather than assigned an organization
implicitly.

## Request requirements

Each endpoint specification must define:

- Authentication requirement.
- Required role or permission.
- Organization scope.
- Input schema and size limits.
- Idempotency behavior.
- State changes and audit events.
- Expected errors.
- Rate limits.
