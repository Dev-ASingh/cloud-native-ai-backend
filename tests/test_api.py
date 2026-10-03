from fastapi.testclient import TestClient
from sqlalchemy import delete

from cloud_native_ai_backend.database import SessionLocal
from cloud_native_ai_backend.main import app
from cloud_native_ai_backend.models import (
    IdempotencyRecord,
    JobRecord,
    MembershipRecord,
    OrganizationRecord,
    UserRecord,
)

client = TestClient(app)
AUTH = {
    "X-User-ID": "user-1",
    "X-Organization-ID": "org-1",
    "X-Role": "member",
}


def setup_function() -> None:
    with SessionLocal() as session:
        session.execute(delete(IdempotencyRecord))
        session.execute(delete(JobRecord))
        session.execute(delete(MembershipRecord))
        session.execute(delete(UserRecord))
        session.execute(delete(OrganizationRecord))
        session.add(UserRecord(id="user-1"))
        session.add(OrganizationRecord(id="org-1"))
        session.add(MembershipRecord(user_id="user-1", organization_id="org-1", role="member"))
        session.add(UserRecord(id="user-2"))
        session.add(OrganizationRecord(id="org-2"))
        session.add(MembershipRecord(user_id="user-2", organization_id="org-2", role="member"))
        session.commit()


def test_health_and_request_id() -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "req_test"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"] == "req_test"


def test_jobs_require_authentication() -> None:
    response = client.get("/api/v1/jobs")

    assert response.status_code == 401


def test_unknown_membership_is_forbidden() -> None:
    response = client.get(
        "/api/v1/jobs",
        headers={
            "X-User-ID": "unknown",
            "X-Organization-ID": "org-1",
            "X-Role": "owner",
        },
    )

    assert response.status_code == 403


def test_role_header_cannot_escalate_membership() -> None:
    response = client.get(
        "/api/v1/me",
        headers={**AUTH, "X-Role": "owner"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "member"


def test_job_is_idempotent_and_organization_scoped() -> None:
    headers = {**AUTH, "Idempotency-Key": "same-request"}
    first = client.post("/api/v1/jobs", headers=headers, json={"payload": {"kind": "demo"}})
    second = client.post("/api/v1/jobs", headers=headers, json={"payload": {"kind": "demo"}})

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]

    other_org = {
        "X-User-ID": "user-2",
        "X-Organization-ID": "org-2",
        "X-Role": "member",
    }
    response = client.get(f"/api/v1/jobs/{first.json()['id']}", headers=other_org)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "job_not_found"


def test_job_can_be_cancelled() -> None:
    headers = {**AUTH, "Idempotency-Key": "cancel-request"}
    created = client.post("/api/v1/jobs", headers=headers, json={"payload": {}})

    response = client.post(
        f"/api/v1/jobs/{created.json()['id']}/cancel",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
