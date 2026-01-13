from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import overview, scaffold, studies
from app.core.config import settings
from app.db.session import engine

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
else:
    logging.getLogger().setLevel(settings.log_level.upper())

app = FastAPI(title=settings.app_name)
logger = logging.getLogger("app")
if settings.environment == "prod" and settings.allow_phi:
    logger.warning("ALLOW_PHI is enabled in prod")

if settings.cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        allow_credentials=settings.cors_allow_credentials,
    )


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get(settings.request_id_header) or str(uuid.uuid4())
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.monotonic() - start) * 1000
        logger.exception(
            "request error method=%s path=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            duration_ms,
            request_id,
        )
        raise
    duration_ms = (time.monotonic() - start) * 1000
    response.headers[settings.request_id_header] = request_id
    logger.info(
        "request completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


@app.get("/_healthz", include_in_schema=False)
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/_readyz", include_in_schema=False)
def readiness(response: Response) -> dict[str, str]:
    if not settings.ready_check_db:
        return {"status": "ok"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error"}
    return {"status": "ok"}

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

app.include_router(overview.router)
app.include_router(studies.router)
app.include_router(scaffold.router)
