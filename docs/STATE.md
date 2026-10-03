# Cloud-Native AI Backend state

## Now

- Latest implementation commit: pending deployment-boundary release slice.
- The API and worker have separate Docker Compose service paths.
- The worker supports configurable identity and long-running polling.
- CI run `37150560158` passed tests, static checks, security gates, container
  build, Trivy scan, and smoke testing.
- A Render blueprint now defines separate API, worker, and PostgreSQL services;
  hosted provisioning is still pending Render account access.
- The repository is public. Hosted deployment and production integrations
  remain intentionally incomplete.

## Next

1. Provision the Render blueprint and review service plans and region.
2. Run the explicit Alembic release migration and verify health/readiness.
3. Execute authenticated job lifecycle smoke tests and record rollback data.
4. Provide the portfolio frontend with a protected, synthetic-data preview
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
