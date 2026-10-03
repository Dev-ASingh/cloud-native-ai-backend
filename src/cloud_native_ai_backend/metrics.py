from threading import Lock

from .telemetry import MetricExporter


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, int] = {}

    def increment(self, name: str, value: int = 1) -> None:
        if value < 0:
            raise ValueError("Metric increments cannot be negative.")
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counters)

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()

    def export(self, exporter: MetricExporter) -> None:
        exporter.export(self.snapshot())


metrics = Metrics()
