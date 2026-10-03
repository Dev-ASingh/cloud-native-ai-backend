from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import delete

from cloud_native_ai_backend.auth import create_session, hash_session_token
from cloud_native_ai_backend.database import SessionLocal
from cloud_native_ai_backend.main import app
from cloud_native_ai_backend.models import (
    IdempotencyRecord,
    JobRecord,
    MembershipRecord,
    OrganizationRecord,
    SessionRecord,
    UserRecord,
)

client = TestClient(app)
TOKEN_1 = "test-session-user-1"
TOKEN_2 = "test-session-user-2"
AUTH = {"Authorization": f"Bearer {TOKEN_1}"}


def setup_function() -> None:
    with SessionLocal() as session:
        session.execute(delete(IdempotencyRecord))
        session.execute(delete(JobRecord))
        session.execute(delete(MembershipRecord))
        session.execute(delete(SessionRecord))
        session.execute(delete(UserRecord))
        session.execute(delete(OrganizationRecord))
        session.add(UserRecord(id="user-1"))
        session.add(OrganizationRecord(id="org-1"))
        session.add(MembershipRecord(user_id="user-1", organization_id="org-1", role="member"))
        session.add(UserRecord(id="user-2"))
        session.add(OrganizationRecord(id="org-2"))
        session.add(MembershipRecord(user_id="user-2", organization_id="org-2", role="member"))
        session.add(
            SessionRecord(
                id="session-1",
                token_hash=hash_session_token(TOKEN_1),
                user_id="user-1",
                organization_id="org-1",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        session.add(
            SessionRecord(
                id="session-2",
                token_hash=hash_session_token(TOKEN_2),
                user_id="user-2",
                organization_id="org-2",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        session.commit()


def test_health_and_request_id() -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "req_test"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"] == "req_test"


def test_jobs_require_authentication() -> None:
    response = client.get("/api/v1/jobs")

    assert response.status_code == 401


def test_unknown_session_is_rejected() -> None:
    response = client.get(
        "/api/v1/jobs",
        headers={"Authorization": "Bearer unknown-token"},
    )

    assert response.status_code == 401


def test_session_resolves_membership_role() -> None:
    response = client.get("/api/v1/me", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["role"] == "member"


def test_job_is_idempotent_and_organization_scoped() -> None:
    headers = {**AUTH, "Idempotency-Key": "same-request"}
    first = client.post("/api/v1/jobs", headers=headers, json={"payload": {"kind": "demo"}})
    second = client.post("/api/v1/jobs", headers=headers, json={"payload": {"kind": "demo"}})

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]

    other_org = {"Authorization": f"Bearer {TOKEN_2}"}
    response = client.get(f"/api/v1/jobs/{first.json()['id']}", headers=other_org)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "job_not_found"


def test_expired_session_is_rejected() -> None:
    with SessionLocal() as session:
        session.add(
            SessionRecord(
                id="expired",
                token_hash=hash_session_token("expired-token"),
                user_id="user-1",
                organization_id="org-1",
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            )
        )
        session.commit()

    response = client.get("/api/v1/me", headers={"Authorization": "Bearer expired-token"})

    assert response.status_code == 401


def test_session_can_be_issued_and_revoked() -> None:
    with SessionLocal() as session:
        token = create_session(session, "user-1", "org-1", timedelta(hours=1))
        stored = session.query(SessionRecord).filter_by(user_id="user-1").order_by(
            SessionRecord.id.desc()
        ).first()
        assert stored is not None
        assert stored.token_hash != token
        assert len(stored.token_hash) == 64

    authenticated = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/me", headers=authenticated).status_code == 200
    assert client.post("/api/v1/auth/session/revoke", headers=authenticated).status_code == 204
    assert client.get("/api/v1/me", headers=authenticated).status_code == 401


def test_job_can_be_cancelled() -> None:
    headers = {**AUTH, "Idempotency-Key": "cancel-request"}
    created = client.post("/api/v1/jobs", headers=headers, json={"payload": {}})

    response = client.post(
        f"/api/v1/jobs/{created.json()['id']}/cancel",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
