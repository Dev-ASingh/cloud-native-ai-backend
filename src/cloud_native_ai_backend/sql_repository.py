from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .domain import DomainError, Job, JobStatus, Principal
from .models import IdempotencyRecord, JobRecord


class SqlAlchemyJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        principal: Principal,
        payload: dict[str, object],
        idempotency_key: str,
    ) -> tuple[Job, bool]:
        existing = self.session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == principal.organization_id,
                IdempotencyRecord.key == idempotency_key,
            )
        )
        if existing is not None:
            record = self._get_record(principal.organization_id, existing.job_id)
            return self._to_domain(record), True

        record = JobRecord(
            organization_id=principal.organization_id,
            created_by=principal.user_id,
            payload=payload,
            status=JobStatus.QUEUED.value,
        )
        self.session.add(record)
        self.session.flush()
        self.session.add(
            IdempotencyRecord(
                organization_id=principal.organization_id,
                key=idempotency_key,
                job_id=record.id,
            )
        )
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.scalar(
                select(IdempotencyRecord).where(
                    IdempotencyRecord.organization_id == principal.organization_id,
                    IdempotencyRecord.key == idempotency_key,
                )
            )
            if existing is None:
                raise
            return self._to_domain(
                self._get_record(principal.organization_id, existing.job_id)
            ), True
        return self._to_domain(record), False

    def list_for(self, organization_id: str, limit: int, offset: int) -> list[Job]:
        records = self.session.scalars(
            select(JobRecord)
            .where(JobRecord.organization_id == organization_id)
            .order_by(JobRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [self._to_domain(record) for record in records]

    def get_for(self, organization_id: str, job_id: UUID) -> Job:
        return self._to_domain(self._get_record(organization_id, job_id))

    def cancel(self, organization_id: str, job_id: UUID) -> Job:
        record = self._get_record(organization_id, job_id)
        if record.status == JobStatus.CANCELLED.value:
            return self._to_domain(record)
        if record.status != JobStatus.QUEUED.value:
            raise DomainError("invalid_job_transition", "The job cannot be cancelled.")
        record.status = JobStatus.CANCELLED.value
        self.session.commit()
        return self._to_domain(record)

    def claim_next(self) -> Job | None:
        record = self.session.scalar(
            select(JobRecord)
            .where(JobRecord.status == JobStatus.QUEUED.value)
            .order_by(JobRecord.created_at.asc())
            .with_for_update(skip_locked=True)
        )
        if record is None:
            return None
        record.status = JobStatus.RUNNING.value
        self.session.commit()
        return self._to_domain(record)

    def complete(self, job_id: UUID) -> Job:
        record = self.session.get(JobRecord, job_id)
        if record is None:
            raise DomainError("job_not_found", "The requested job was not found.")
        if record.status != JobStatus.RUNNING.value:
            raise DomainError("invalid_job_transition", "The job cannot be completed.")
        record.status = JobStatus.COMPLETED.value
        self.session.commit()
        return self._to_domain(record)

    def _get_record(self, organization_id: str, job_id: UUID) -> JobRecord:
        record = self.session.scalar(
            select(JobRecord).where(
                JobRecord.id == job_id,
                JobRecord.organization_id == organization_id,
            )
        )
        if record is None:
            raise DomainError("job_not_found", "The requested job was not found.")
        return record

    @staticmethod
    def _to_domain(record: JobRecord) -> Job:
        return Job(
            id=record.id,
            organization_id=record.organization_id,
            created_by=record.created_by,
            payload=record.payload,
            status=JobStatus(record.status),
            created_at=record.created_at,
        )
