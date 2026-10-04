# Cloud-Native AI Backend state

## Now

- Latest implementation commit: `ef6a7dd` (guarded on-demand AWS demo slice).
- The API and worker have separate Docker Compose service paths.
- The worker supports configurable identity and long-running polling.
- CI run `37150560158` passed tests, static checks, security gates, container
  build, Trivy scan, and smoke testing.
- An on-demand AWS CloudFormation stack now defines the API, worker, and
  PostgreSQL demo topology.
- GitHub Actions uses OIDC short-lived credentials; no AWS access keys are
  stored in the repository or portfolio.
- The repository is public. Hosted deployment and production integrations
  remain intentionally incomplete.

## Next

1. Create the one-time AWS OIDC provider and restricted role from
   `infra/aws/README.md`.
2. Add the role ARN, region, VPC, subnet, and budget email to GitHub Actions.
3. Run Start Demo, verify health/readiness and job lifecycle, then run Stop
   Demo and verify the CloudFormation stack is absent.
4. Add the verified temporary API URL only as runtime evidence; never commit it
   as a permanent preview URL.

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
