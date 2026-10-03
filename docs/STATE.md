# Cloud-Native AI Backend state

## Now

- Latest implementation commit: pending this release slice.
- The API and worker have separate Docker Compose service paths.
- The worker supports configurable identity and long-running polling.
- CI run `37150560158` passed tests, static checks, security gates, container
  build, Trivy scan, and smoke testing.
- No hosted preview deployment exists yet.
- The repository remains private until the public-release security gate is
  explicitly completed.

## Next

1. Choose a container-capable hosting provider and managed PostgreSQL service.
2. Add production environment configuration, secret handling, and explicit
   migration execution.
3. Deploy API and worker as separate services.
4. Add deployment health/readiness smoke checks and rollback documentation.
5. Provide the portfolio frontend with a protected, synthetic-data preview
   boundary.

## Remaining production work

- Production identity and account lifecycle.
- Replaceable broker or queue adapter.
- Approval and delivery workflow.
- Artifact storage and retention controls.
- Provider adapters and evaluation fixtures.
- Centralized telemetry export.
- Terraform or equivalent deployment infrastructure.
- PostgreSQL integration coverage for lease, retry, and audit transitions.
- Image signing, SBOM, provenance, cost, evaluation, and incident runbooks.
