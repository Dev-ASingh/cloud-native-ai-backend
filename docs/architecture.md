# Architecture

## Scope

The first release is a secure asynchronous job platform. It accepts a
validated request, records it, dispatches work, stores the result, and
requires approval before a sensitive delivery action.

## Boundary

```text
HTTP client
  |
  v
API service
  |-- identity and authorization
  |-- request validation and idempotency
  |-- PostgreSQL
  |-- queue adapter
  |       |
  |       v
  |    worker
  |      |-- provider adapter
  |      |-- artifact store
  |      |-- audit event writer
  |
  +-- health, readiness, metrics, and trace context
```

## Component responsibilities

### API service

Owns transport concerns, authentication, authorization, request validation,
idempotency keys, pagination, response schemas, and stable error envelopes. It
does not execute long-running work inline.

### Domain layer

Owns job state transitions, approval rules, retry classification, and
organization-scoped invariants. It must not import HTTP, queue, or cloud SDK
details.

### Persistence layer

Owns transactions, migrations, query boundaries, and optimistic concurrency.
Every organization-scoped query must carry an authorization context.

### Queue adapter

Owns dispatch, acknowledgement, visibility timeout, retry metadata, and
dead-letter behavior. The domain layer depends on a protocol, not Redis APIs.

### Worker

Owns execution orchestration and provider adapters. It records each transition,
enforces timeouts, handles cancellation, and never writes secrets to logs.

### Artifact store

Owns content persistence through a narrow interface. Local storage is for
development; production storage must enforce encryption, access control, and
retention.

### Audit writer

Appends actor, action, target, request ID, timestamp, and outcome. Application
code cannot update or delete existing audit records.

## State model

```text
accepted -> queued -> running -> awaiting_approval -> approved -> delivered
                  |       |              |              |
                  v       v              v              v
               cancelled failed       expired        rejected
```

Only the domain service may perform transitions. Invalid transitions are
rejected and recorded as security-relevant events where appropriate.

## Data isolation

Every organization-owned entity includes `organization_id`. Authorization is
checked before retrieval and mutation. Object identifiers are not authorization
boundaries.

## Deployment shape

Local development uses Docker Compose for PostgreSQL, Redis, API, and worker.
The cloud deployment uses the same application boundaries with managed
database, queue, object storage, secrets, and observability services. The
provider mapping will be recorded in an ADR before Terraform is written.

## Current implementation boundary

Milestone 2 uses SQLAlchemy persistence with Alembic-managed schema changes and
a local SQLite default. PostgreSQL is supported through configuration.
Development-only identity headers identify a request, but active persisted
memberships determine authorization and role. This remains a replaceable
adapter, not production authentication. Durable queueing and a real identity
boundary are still required before the repository can be considered
deployable.
