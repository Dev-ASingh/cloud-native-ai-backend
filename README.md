# Cloud-Native AI Backend

Secure, observable, asynchronous backend foundations for trustworthy AI
workloads.

![System architecture overview](assets/README-architecture.svg)

Version one deliberately uses deterministic work so that the backend, security,
reliability, delivery, and operations can be evaluated before adding model
variability.

## Status

The current implementation includes a database-backed queue boundary, worker
leases, audit events, scoped metrics, and structured telemetry. It uses
development-only request headers and a local SQLite default; PostgreSQL is
supported through `DATABASE_URL`. No production or customer data is used.

Database schema changes are managed with Alembic:

```bash
alembic upgrade head
```

## Design goals

- Versioned API with explicit schemas and stable errors.
- Organization-scoped authorization and deny-by-default access.
- Idempotent asynchronous jobs with bounded retries.
- Human approval before sensitive delivery.
- Append-only audit events without secret leakage.
- Reproducible local and cloud deployment.
- Measurable quality, reliability, latency, and cost.

## Planned stack

- Python 3.12+
- FastAPI and Pydantic
- SQLAlchemy 2 and Alembic
- PostgreSQL
- Redis-backed queue adapter
- Pytest
- Docker Compose
- Terraform
- GitHub Actions
- OpenTelemetry-compatible instrumentation

The final queue and cloud provider choices remain subject to the documented
architecture decision records. Application code will depend on interfaces
rather than vendor-specific calls.

## Repository map

- `docs/architecture.md` — system boundary and component responsibilities.
- `docs/threat-model.md` — assets, trust boundaries, abuse cases, and controls.
- `docs/api-contract.md` — initial endpoint and error contract.
- `docs/test-strategy.md` — unit, integration, contract, failure, and security
  test gates.
- `docs/adr/` — decision records.
- `src/` — application code after the design contract is accepted.
- `tests/` — executable evidence for every supported behavior.

## Local development

Install development dependencies and run the API against SQLite:

```bash
python -m pip install -e ".[dev]"
uvicorn cloud_native_ai_backend.main:app --reload
```

For PostgreSQL-backed development, start the database and set the URL:

```bash
docker compose up -d postgres
export DATABASE_URL=postgresql+psycopg://backend:backend@localhost:5432/backend
alembic upgrade head
uvicorn cloud_native_ai_backend.main:app --reload
```

The Compose file provisions only the database. Application and worker
processes remain explicit local commands so their logs and lifecycle are
visible during development.

The current bearer-session verifier is an identity boundary, but session
issuance is not exposed as a public login flow. Authenticated users can revoke
their current session. Do not add credentials, customer data, or `.env` files
to this repository.

For tests and controlled local development, seed a session record and send:

```text
Authorization: Bearer <session-token>
```

Job creation also requires a bounded `Idempotency-Key` header. Created jobs are
durably stored as `queued`; the development worker claims them as `running`,
executes a deterministic handler, and marks them `completed` or retries them
through the lease boundary. Provider execution and approval-gated delivery are
not yet implemented. Worker leases expire and requeue jobs; after three
attempts, a failed job becomes terminal.

Run one development worker pass after applying migrations:

```bash
python -m cloud_native_ai_backend.worker
```

## Evidence standard

This project is not portfolio-ready until CI is green, security controls are
tested, deployment is reproducible, operational behavior is documented, and
the public repository contains no private or client material.
