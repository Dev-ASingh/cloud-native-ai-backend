from datetime import UTC, datetime
from uuid import uuid4

import pytest

from cloud_native_ai_backend.domain import Job
from cloud_native_ai_backend.providers import ProviderRegistry, ProviderUnavailable


def test_default_provider_is_deterministic() -> None:
    job = Job(uuid4(), "org-1", "user-1", {}, created_at=datetime.now(UTC))

    ProviderRegistry().executor_for(job)(job)


def test_unknown_provider_fails_closed() -> None:
    job = Job(
        uuid4(),
        "org-1",
        "user-1",
        {"provider": "external-model"},
        created_at=datetime.now(UTC),
    )

    with pytest.raises(ProviderUnavailable, match="external-model"):
        ProviderRegistry().executor_for(job)
