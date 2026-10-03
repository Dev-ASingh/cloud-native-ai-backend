import logging
from typing import Protocol

from sqlalchemy.orm import Session

from .database import SessionLocal
from .domain import Job
from .sql_repository import SqlAlchemyJobRepository

logger = logging.getLogger(__name__)


class JobExecutor(Protocol):
    def __call__(self, job: Job) -> None: ...


def execute_deterministic_job(job: Job) -> None:
    """Development executor used until provider adapters are introduced."""
    if job.payload.get("should_fail") is True:
        raise RuntimeError("deterministic job failure requested")


class Worker:
    def __init__(
        self,
        session: Session,
        worker_id: str,
        executor: JobExecutor = execute_deterministic_job,
    ) -> None:
        self.repository = SqlAlchemyJobRepository(session)
        self.worker_id = worker_id
        self.executor = executor

    def run_once(self) -> bool:
        job = self.repository.claim_next(self.worker_id)
        if job is None:
            return False

        try:
            self.executor(job)
        except Exception:
            logger.exception("Job execution failed", extra={"job_id": str(job.id)})
            self.repository.fail(job.id, self.worker_id)
        else:
            self.repository.complete(job.id, self.worker_id)
        return True


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as session:
        Worker(session, "development-worker").run_once()


if __name__ == "__main__":
    main()
