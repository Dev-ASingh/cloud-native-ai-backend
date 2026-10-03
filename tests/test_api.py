from fastapi.testclient import TestClient

from cloud_native_ai_backend.api import repository
from cloud_native_ai_backend.main import app

client = TestClient(app)
AUTH = {
    "X-User-ID": "user-1",
    "X-Organization-ID": "org-1",
    "X-Role": "member",
}


def setup_function() -> None:
    repository._jobs.clear()
    repository._idempotency.clear()


def test_health_and_request_id() -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "req_test"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"] == "req_test"


def test_jobs_require_authentication() -> None:
    response = client.get("/api/v1/jobs")

    assert response.status_code == 401


def test_job_is_idempotent_and_organization_scoped() -> None:
    headers = {**AUTH, "Idempotency-Key": "same-request"}
    first = client.post("/api/v1/jobs", headers=headers, json={"payload": {"kind": "demo"}})
    second = client.post("/api/v1/jobs", headers=headers, json={"payload": {"kind": "demo"}})

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["id"] == second.json()["id"]

    other_org = {**AUTH, "X-Organization-ID": "org-2"}
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
