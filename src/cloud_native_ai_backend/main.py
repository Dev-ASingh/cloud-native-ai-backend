import logging
from collections.abc import Awaitable, Callable
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from .api import router
from .config import get_settings
from .database import initialize_database
from .metrics import metrics
from .telemetry import configure_logging, request_id_context

settings = get_settings()
settings.validate_runtime()
configure_logging()
if settings.auto_create_database:
    initialize_database()
app = FastAPI(title=settings.app_name, version="0.1.0")
logger = logging.getLogger(__name__)


@app.middleware("http")
async def request_context(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request.state.request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex}")
    token = request_id_context.set(request.state.request_id)
    started = monotonic()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response
    finally:
        metrics.increment("http.requests")
        logger.info(
            "HTTP request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round((monotonic() - started) * 1000, 2),
            },
        )
        request_id_context.reset(token)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, _exception: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
                "request_id": request.state.request_id,
            }
        },
    )


app.include_router(router)
