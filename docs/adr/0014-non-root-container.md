# ADR 0014: Ship a Minimal Non-Root API Container

- Status: Accepted
- Date: 2026-10-04

## Context

The service needs a reproducible deployment artifact that can be scanned and
run independently from the development environment. Running the API as root
would make a container compromise unnecessarily broad.

## Decision

The repository will build a small Python 3.12 runtime image, install only the
application runtime dependencies, omit development and documentation files,
and run the API as a dedicated non-root `app` user. Database migrations remain
an explicit release operation.

## Consequences

- CI can scan the exact artifact used for deployment.
- The container has a smaller attack surface than the development environment.
- Deployment automation must run migrations with an explicit, controlled step.
