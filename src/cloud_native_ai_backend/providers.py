from collections.abc import Callable
from typing import Protocol

from .domain import Job


class ProviderAdapter(Protocol):
    name: str

    def execute(self, job: Job) -> None: ...


class ProviderUnavailable(RuntimeError):
    """Raised when a job selects an adapter that is not configured."""


class DeterministicProvider:
    name = "deterministic"

    def execute(self, job: Job) -> None:
        if job.payload.get("should_fail") is True:
            raise RuntimeError("deterministic job failure requested")


ProviderFactory = Callable[[], ProviderAdapter]


class ProviderRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {
            DeterministicProvider.name: DeterministicProvider,
        }

    def register(self, name: str, factory: ProviderFactory) -> None:
        if not name or not name.strip():
            raise ValueError("Provider name is required.")
        self._factories[name] = factory

    def executor_for(self, job: Job) -> Callable[[Job], None]:
        requested = job.payload.get("provider", DeterministicProvider.name)
        if not isinstance(requested, str) or requested not in self._factories:
            raise ProviderUnavailable(f"Provider is not configured: {requested!r}")
        adapter = self._factories[requested]()
        return adapter.execute


providers = ProviderRegistry()
