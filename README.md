# Cloud-Native AI Backend

Secure asynchronous backend foundations for trustworthy AI workloads.

![System architecture overview](assets/README-architecture.svg)

## Status

This repository is an active engineering foundation. It is not presented as a
finished hosted product or as evidence of production customer usage.

The implemented boundary includes:

- FastAPI API routes with stable response and error models.
- Organization-scoped authorization backed by persisted memberships.
- Opaque bearer sessions with expiration and authenticated revocation.
- Idempotent, database-backed jobs with queued, running, completed, cancelled,
  and failed transitions.
- Worker leases, expiry recovery, bounded retries, and terminal failures.
- Append-only organization-scoped audit events.
- Request-ID-correlated JSON logs and organization-scoped operational metrics.
- SQLite for local development and PostgreSQL for integration or deployment.
- Separate API and worker container paths in Docker Compose.
- Non-root container execution and CI security gates.

The deterministic executor is intentional. Provider adapters, approval-gated
delivery, artifact storage, and hosted deployment remain explicit next
milestones rather than implied capabilities.

## Architecture

```text
client
  |
  v
API service ---- PostgreSQL
  |
  v
durable job state
  |
  v
worker process
  |
  +-- deterministic executor
  +-- audit events
  +-- metrics and structured logs
```

The domain and persistence boundaries are designed so that a real broker,
provider adapter, artifact store, and centralized telemetry backend can be
introduced without moving vendor-specific code into the domain layer.

Detailed responsibilities and invariants are documented in
`docs/architecture.md`. Security boundaries are documented in
`docs/threat-model.md`.

## Technology

- Python 3.12+
- FastAPI and Pydantic
- SQLAlchemy 2 and Alembic
- SQLite for local development
- PostgreSQL through `psycopg`
- Docker and Docker Compose
- Pytest, Ruff, and mypy
- GitHub Actions, pip-audit, credential scanning, and Trivy

## Local development

Install the project and development tools:

```bash
python -m pip install -e ".[dev]"
```

Run the API with the default SQLite database:

```bash
uvicorn cloud_native_ai_backend.main:app --reload
```

Run the full local PostgreSQL topology:

```bash
docker compose up --build
```

The Compose topology contains PostgreSQL, API, and worker services. The API
listens on `http://localhost:8000`. Migrations remain an explicit release
operation:

```bash
docker compose run --rm api alembic upgrade head
```

The readiness endpoint performs a database probe:

```text
GET /api/v1/health
GET /api/v1/ready
```

The worker uses `WORKER_ID` and `WORKER_POLL_INTERVAL_SECONDS` configuration.
It never logs job payloads or credentials.

## Verification

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src tests
.venv/bin/pip-audit
python scripts/check_secrets.py
```

CI additionally applies PostgreSQL migrations, builds the production image,
runs Trivy against the image, and performs a container health smoke test.

## API boundary

The current API includes health and readiness checks, authenticated identity
inspection, job creation, listing, retrieval, cancellation, session
revocation, and operational metrics. Authentication issuance remains a
server-side development boundary and is not exposed as a public login flow.

The following capabilities are intentionally not claimed as complete:

- Production identity and account lifecycle.
- External broker or queue adapter.
- Provider or model execution.
- Approval and delivery workflow.
- Artifact storage and retention controls.
- Centralized logs, metrics, and tracing.
- Cloud infrastructure and public preview deployment.

## Repository map

- `src/cloud_native_ai_backend/` - application and worker code.
- `alembic/` - migration environment and versioned schema changes.
- `tests/` - executable API, repository, worker, and database evidence.
- `docs/architecture.md` - system boundary and responsibilities.
- `docs/threat-model.md` - assets, trust boundaries, and abuse cases.
- `docs/api-contract.md` - endpoint and error contract.
- `docs/test-strategy.md` - test and security gates.
- `docs/adr/` - recorded architecture decisions.
- `assets/README-architecture.svg` - repository documentation artwork.

## License

MIT
