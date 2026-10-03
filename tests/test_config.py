import pytest

from cloud_native_ai_backend.config import Settings


def test_production_rejects_automatic_schema_creation() -> None:
    settings = Settings(app_env="production", auto_create_database=True)

    with pytest.raises(ValueError, match="AUTO_CREATE_DATABASE"):
        settings.validate_runtime()


def test_worker_poll_interval_must_be_positive() -> None:
    settings = Settings(worker_poll_interval_seconds=0)

    with pytest.raises(ValueError, match="WORKER_POLL_INTERVAL_SECONDS"):
        settings.validate_runtime()
