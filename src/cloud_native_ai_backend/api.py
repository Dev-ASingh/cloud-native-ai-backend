from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .auth import hash_session_token, revoke_session
from .config import Settings, get_settings
from .database import get_session
from .domain import DomainError, Job, Principal
from .metrics import metrics
from .models import JobRecord, MembershipRecord, SessionRecord
from .sql_repository import SqlAlchemyJobRepository

router = APIRouter(prefix="/api/v1")


class JobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: dict[str, object] = Field(default_factory=dict, max_length=20)


class JobResponse(BaseModel):
    id: UUID
    organization_id: str
    created_by: str
    payload: dict[str, object]
    status: str

    @classmethod
    def from_domain(cls, job: Job) -> "JobResponse":
        return cls(
            id=job.id,
            organization_id=job.organization_id,
            created_by=job.created_by,
            payload=job.payload,
            status=job.status.value,
        )


class JobListResponse(BaseModel):
    items: list[JobResponse]
    limit: int
    offset: int


class PrincipalResponse(BaseModel):
    user_id: str
    organization_id: str
    role: str


def get_repository(session: Session = Depends(get_session)) -> SqlAlchemyJobRepository:
    return SqlAlchemyJobRepository(session)


def get_principal(
    session: Session = Depends(get_session),
    authorization: str | None = Header(default=None),
) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not token or len(token) > 512:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    session_record = session.scalar(
        select(SessionRecord).where(
            SessionRecord.token_hash == hash_session_token(token),
            SessionRecord.revoked.is_(False),
            SessionRecord.expires_at > datetime.now(UTC),
        )
    )
    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    membership = session.scalar(
        select(MembershipRecord).where(
            MembershipRecord.user_id == session_record.user_id,
            MembershipRecord.organization_id == session_record.organization_id,
            MembershipRecord.active.is_(True),
        )
    )
    if membership is None or session_record.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization membership is required.",
        )
    return Principal(
        user_id=session_record.user_id,
        organization_id=session_record.organization_id,
        role=membership.role,
    )


@router.post("/auth/session/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_current_session(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
    _principal: Principal = Depends(get_principal),
) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    revoke_session(session, token)


def handle_domain_error(error: DomainError, request: Request) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if error.code == "job_not_found"
        else status.HTTP_409_CONFLICT
    )
    return HTTPException(
        status_code=status_code,
        detail={"code": error.code, "message": error.message, "request_id": request.state.request_id},
    )


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@router.get("/ready")
def ready(
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    if not settings.readiness_dependency:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Not ready.")
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Required dependencies are unavailable.",
        ) from error
    return {"status": "ready"}


@router.get("/metrics")
def operational_metrics(
    session: Session = Depends(get_session),
    principal: Principal = Depends(get_principal),
) -> dict[str, int]:
    counts = {
        "jobs.queued": 0,
        "jobs.running": 0,
        "jobs.completed": 0,
        "jobs.failed": 0,
        "jobs.cancelled": 0,
    }
    rows = session.execute(
        select(JobRecord.status, func.count())
        .where(JobRecord.organization_id == principal.organization_id)
        .group_by(JobRecord.status)
    )
    for status_name, count in rows:
        key = f"jobs.{status_name}"
        if key in counts:
            counts[key] = count
    counts.update(metrics.snapshot())
    return counts


@router.get("/me", response_model=PrincipalResponse)
def me(principal: Principal = Depends(get_principal)) -> PrincipalResponse:
    return PrincipalResponse.model_validate(principal, from_attributes=True)


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    request: Request,
    body: JobCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(get_principal),
    repo: SqlAlchemyJobRepository = Depends(get_repository),
) -> JobResponse:
    if not idempotency_key or len(idempotency_key) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "idempotency_key_required",
                "message": "Idempotency-Key is required.",
                "request_id": request.state.request_id,
            },
        )
    job, _ = repo.create(principal, body.payload, idempotency_key)
    return JobResponse.from_domain(job)


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    principal: Principal = Depends(get_principal),
    repo: SqlAlchemyJobRepository = Depends(get_repository),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> JobListResponse:
    return JobListResponse(
        items=[JobResponse.from_domain(job) for job in repo.list_for(principal.organization_id, limit, offset)],
        limit=limit,
        offset=offset,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    request: Request,
    job_id: UUID,
    principal: Principal = Depends(get_principal),
    repo: SqlAlchemyJobRepository = Depends(get_repository),
) -> JobResponse:
    try:
        return JobResponse.from_domain(repo.get_for(principal.organization_id, job_id))
    except DomainError as error:
        raise handle_domain_error(error, request) from error


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(
    request: Request,
    job_id: UUID,
    principal: Principal = Depends(get_principal),
    repo: SqlAlchemyJobRepository = Depends(get_repository),
) -> JobResponse:
    try:
        return JobResponse.from_domain(repo.cancel(principal.organization_id, job_id))
    except DomainError as error:
        raise handle_domain_error(error, request) from error
