# Deployment

The repository includes a Render blueprint for the API, worker, and PostgreSQL
services. The API and worker use the same image and database, but they run as
separate services so worker polling is not coupled to HTTP availability.

## Render release procedure

1. Create a Render Blueprint from this repository using `render.yaml`.
2. Review the generated service names, region, plan, and PostgreSQL disk size.
3. Confirm `DATABASE_URL` is supplied from the managed database connection
   string.
4. Run the migration command as an explicit release operation:

   ```bash
   alembic upgrade head
   ```

5. Deploy the API and worker.
6. Verify `/api/v1/health` and `/api/v1/ready`.
7. Submit an authenticated idempotent job and verify queued, running, and
   completed transitions.
8. Record the deployment URL, migration revision, smoke-test result, and
   rollback target in the release record.

Production disables SQLAlchemy `create_all`. A deployment must use Alembic
migrations and must fail fast if `AUTO_CREATE_DATABASE=true` is supplied with
`APP_ENV=production`.

## Current deployment boundary

The deployment is a reliable API and worker foundation. It does not claim a
production model provider, approval workflow, artifact store, centralized
telemetry export, or public login/account lifecycle. Those capabilities must be
implemented and tested before calling the system a complete production AI
platform.
