from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from .config import Settings, get_settings
from .domain import DomainError, Job, JobRepository, Principal

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


def get_repository() -> JobRepository:
    return repository


def get_principal(
    x_user_id: str | None = Header(default=None),
    x_organization_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> Principal:
    if not x_user_id or not x_organization_id or not x_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    if len(x_user_id) > 128 or len(x_organization_id) > 128 or len(x_role) > 64:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    return Principal(
        user_id=x_user_id,
        organization_id=x_organization_id,
        role=x_role,
    )


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
def ready(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    if not settings.readiness_dependency:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Not ready.")
    return {"status": "ready"}


@router.get("/me", response_model=PrincipalResponse)
def me(principal: Principal = Depends(get_principal)) -> PrincipalResponse:
    return PrincipalResponse.model_validate(principal, from_attributes=True)


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    request: Request,
    body: JobCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(get_principal),
    repo: JobRepository = Depends(get_repository),
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
    repo: JobRepository = Depends(get_repository),
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
    repo: JobRepository = Depends(get_repository),
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
    repo: JobRepository = Depends(get_repository),
) -> JobResponse:
    try:
        return JobResponse.from_domain(repo.cancel(principal.organization_id, job_id))
    except DomainError as error:
        raise handle_domain_error(error, request) from error


repository = JobRepository()
