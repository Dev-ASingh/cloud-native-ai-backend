# Cloud-Native AI Backend

Secure, observable, asynchronous backend foundations for trustworthy AI
workloads.

This repository is Flagship Project 1 in Ashish Singh's Agentic AI and Applied
AI Systems roadmap. Version one deliberately uses deterministic work so that
the backend, security, reliability, delivery, and operations can be evaluated
before adding model variability.

## Status

Milestone 2 — database-backed synchronous core. The current implementation
uses development-only request headers and a local SQLite default; PostgreSQL is
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

Milestone 1 now exposes a minimal local API. Install development dependencies
and run:

```bash
python -m pip install -e ".[dev]"
uvicorn cloud_native_ai_backend.main:app --reload
```

The current authentication headers are an explicit development boundary, not a
production identity system. Do not add credentials, customer data, or `.env`
files to this repository.

For authenticated development requests, send:

```text
X-User-ID: user-1
X-Organization-ID: org-1
X-Role: member
```

Job creation also requires a bounded `Idempotency-Key` header.

## Evidence standard

This project is not portfolio-ready until CI is green, security controls are
tested, deployment is reproducible, operational behavior is documented, and
the public repository contains no private or client material.
