from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import delete

from cloud_native_ai_backend.audit import AuditWriter
from cloud_native_ai_backend.auth import create_session, hash_session_token
from cloud_native_ai_backend.database import SessionLocal
from cloud_native_ai_backend.domain import Principal
from cloud_native_ai_backend.main import app
from cloud_native_ai_backend.models import (
    AuditEventRecord,
    IdempotencyRecord,
    JobRecord,
    MembershipRecord,
    OrganizationRecord,
    SessionRecord,
    UserRecord,
)
from cloud_native_ai_backend.sql_repository import SqlAlchemyJobRepository
from cloud_native_ai_backend.worker import Worker

client = TestClient(app)
TOKEN_1 = "test-session-user-1"
TOKEN_2 = "test-session-user-2"
AUTH = {"Authorization": f"Bearer {TOKEN_1}"}


def setup_function() -> None:
    with SessionLocal() as session:
        session.execute(delete(IdempotencyRecord))
        session.execute(delete(AuditEventRecord))
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


def test_worker_claims_and_completes_queued_job() -> None:
    with SessionLocal() as session:
        repository = SqlAlchemyJobRepository(session)
        created, replayed = repository.create(
            Principal(user_id="user-1", organization_id="org-1", role="member"),
            {"kind": "worker-test"},
            "worker-request",
        )
        assert replayed is False
        assert created.status.value == "queued"

        claimed = repository.claim_next("worker-1")
        assert claimed is not None
        assert claimed.id == created.id
        assert claimed.status.value == "running"

        completed = repository.complete(created.id, "worker-1")
        assert completed.status.value == "completed"
        assert repository.claim_next("worker-1") is None


def test_expired_lease_is_requeued_and_retried() -> None:
    with SessionLocal() as session:
        repository = SqlAlchemyJobRepository(session)
        created, _ = repository.create(
            Principal(user_id="user-1", organization_id="org-1", role="member"),
            {"kind": "retry-test"},
            "retry-request",
        )
        first = repository.claim_next(
            "worker-1",
            lease_duration=timedelta(seconds=1),
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert first is not None
        second = repository.claim_next(
            "worker-2",
            now=datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC),
        )
        assert second is not None
        assert second.id == created.id
        assert second.attempt == 2


def test_failed_job_becomes_terminal_after_max_attempts() -> None:
    with SessionLocal() as session:
        repository = SqlAlchemyJobRepository(session)
        created, _ = repository.create(
            Principal(user_id="user-1", organization_id="org-1", role="member"),
            {"kind": "failure-test"},
            "failure-request",
        )
        for attempt in range(3):
            claimed = repository.claim_next(
                f"worker-{attempt}",
                lease_duration=timedelta(seconds=1),
                now=datetime(2026, 1, 1, 0, 0, attempt * 2, tzinfo=UTC),
            )
            assert claimed is not None
            result = repository.fail(created.id, f"worker-{attempt}")
            if attempt < 2:
                assert result.status.value == "queued"
            else:
                assert result.status.value == "failed"


def test_worker_runs_executor_and_completes_job() -> None:
    with SessionLocal() as session:
        repository = SqlAlchemyJobRepository(session)
        created, _ = repository.create(
            Principal(user_id="user-1", organization_id="org-1", role="member"),
            {"kind": "worker-process-test"},
            "worker-process-request",
        )
        executed: list[str] = []
        worker = Worker(
            session,
            "worker-process-1",
            executor=lambda job: executed.append(str(job.id)),
        )

        assert worker.run_once() is True
        assert executed == [str(created.id)]
        assert repository.get_for("org-1", created.id).status.value == "completed"
        event = session.query(AuditEventRecord).one()
        assert event.action == "job.execution"
        assert event.outcome == "completed"
        assert event.event_metadata == {"attempt": 1}
        assert worker.run_once() is False


def test_worker_records_executor_failure_for_retry() -> None:
    with SessionLocal() as session:
        repository = SqlAlchemyJobRepository(session)
        created, _ = repository.create(
            Principal(user_id="user-1", organization_id="org-1", role="member"),
            {"should_fail": True},
            "worker-failure-request",
        )
        worker = Worker(session, "worker-failure-1")

        assert worker.run_once() is True
        assert repository.get_for("org-1", created.id).status.value == "queued"
        event = session.query(AuditEventRecord).one()
        assert event.outcome == "queued"
        assert "should_fail" not in event.event_metadata


def test_audit_writer_does_not_store_payloads() -> None:
    with SessionLocal() as session:
        AuditWriter(session).append(
            organization_id="org-1",
            actor_id="worker-1",
            action="job.execution",
            target_id="job-1",
            outcome="completed",
            metadata={"attempt": 1},
        )
        session.commit()
        event = session.query(AuditEventRecord).one()
        assert event.event_metadata == {"attempt": 1}
