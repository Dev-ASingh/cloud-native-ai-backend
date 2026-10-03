import json
import logging
from collections.abc import Mapping
from contextvars import ContextVar
from typing import Protocol

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class MetricExporter(Protocol):
    def export(self, values: Mapping[str, int]) -> None: ...


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("method", "path", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                event[field] = value
        request_id = request_id_context.get()
        if request_id is not None:
            event["request_id"] = request_id
        return json.dumps(event, sort_keys=True)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


class InMemoryMetricExporter:
    def __init__(self) -> None:
        self.last_export: dict[str, int] = {}

    def export(self, values: Mapping[str, int]) -> None:
        self.last_export = dict(values)
