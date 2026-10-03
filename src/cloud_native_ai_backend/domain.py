from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class JobStatus(StrEnum):
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    organization_id: str
    role: str


@dataclass(slots=True)
class Job:
    id: UUID
    organization_id: str
    created_by: str
    payload: dict[str, object]
    status: JobStatus = JobStatus.ACCEPTED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class DomainError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class JobRepository:
    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}
        self._idempotency: dict[tuple[str, str], UUID] = {}

    def create(
        self,
        principal: Principal,
        payload: dict[str, object],
        idempotency_key: str,
    ) -> tuple[Job, bool]:
        key = (principal.organization_id, idempotency_key)
        existing_id = self._idempotency.get(key)
        if existing_id is not None:
            return self._jobs[existing_id], True

        job = Job(
            id=uuid4(),
            organization_id=principal.organization_id,
            created_by=principal.user_id,
            payload=payload,
        )
        self._jobs[job.id] = job
        self._idempotency[key] = job.id
        return job, False

    def list_for(self, organization_id: str, limit: int, offset: int) -> list[Job]:
        jobs = [
            job for job in self._jobs.values() if job.organization_id == organization_id
        ]
        return sorted(jobs, key=lambda job: job.created_at, reverse=True)[offset : offset + limit]

    def get_for(self, organization_id: str, job_id: UUID) -> Job:
        job = self._jobs.get(job_id)
        if job is None or job.organization_id != organization_id:
            raise DomainError("job_not_found", "The requested job was not found.")
        return job

    def cancel(self, organization_id: str, job_id: UUID) -> Job:
        job = self.get_for(organization_id, job_id)
        if job.status == JobStatus.CANCELLED:
            return job
        if job.status != JobStatus.ACCEPTED:
            raise DomainError("invalid_job_transition", "The job cannot be cancelled.")
        job.status = JobStatus.CANCELLED
        return job
