import logging
import time
from typing import Protocol

from sqlalchemy.orm import Session

from .audit import AuditWriter
from .config import get_settings
from .database import SessionLocal
from .domain import Job
from .metrics import metrics
from .providers import ProviderUnavailable, providers
from .sql_repository import SqlAlchemyJobRepository

logger = logging.getLogger(__name__)


class JobExecutor(Protocol):
    def __call__(self, job: Job) -> None: ...


def execute_job(job: Job) -> None:
    providers.executor_for(job)(job)


class Worker:
    def __init__(
        self,
        session: Session,
        worker_id: str,
        executor: JobExecutor = execute_job,
    ) -> None:
        self.repository = SqlAlchemyJobRepository(session)
        self.audit = AuditWriter(session)
        self.worker_id = worker_id
        self.executor = executor

    def run_once(self) -> bool:
        job = self.repository.claim_next(self.worker_id)
        if job is None:
            metrics.increment("worker.empty_polls")
            return False
        metrics.increment("worker.jobs_claimed")
        metrics.increment("worker.attempts")

        try:
            self.executor(job)
        except ProviderUnavailable:
            logger.exception("Job provider is unavailable", extra={"job_id": str(job.id)})
            failed = self.repository.fail(job.id, self.worker_id, max_attempts=job.attempt)
            metrics.increment("worker.jobs_failed")
            metrics.increment("worker.jobs_terminally_failed")
            self.audit.append(
                organization_id=job.organization_id,
                actor_id=self.worker_id,
                action="job.execution",
                target_id=job.id,
                outcome=failed.status.value,
                metadata={"attempt": failed.attempt, "reason": "provider_unavailable"},
            )
        except Exception:
            logger.exception("Job execution failed", extra={"job_id": str(job.id)})
            failed = self.repository.fail(job.id, self.worker_id)
            metrics.increment("worker.jobs_failed")
            if failed.status.value == "queued":
                metrics.increment("worker.jobs_retried")
            else:
                metrics.increment("worker.jobs_terminally_failed")
            self.audit.append(
                organization_id=job.organization_id,
                actor_id=self.worker_id,
                action="job.execution",
                target_id=job.id,
                outcome=failed.status.value,
                metadata={"attempt": failed.attempt},
            )
        else:
            completed = self.repository.complete(job.id, self.worker_id)
            metrics.increment("worker.jobs_completed")
            self.audit.append(
                organization_id=job.organization_id,
                actor_id=self.worker_id,
                action="job.execution",
                target_id=job.id,
                outcome=completed.status.value,
                metadata={"attempt": completed.attempt},
            )
        self.repository.session.commit()
        return True

    def run_forever(self, poll_interval_seconds: float) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        while True:
            if not self.run_once():
                time.sleep(poll_interval_seconds)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    settings.validate_runtime()
    with SessionLocal() as session:
        Worker(session, settings.worker_id).run_forever(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
