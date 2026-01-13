from __future__ import annotations

import ipaddress
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import overview, scaffold, studies
from app.core.config import settings
from app.core.security import get_session_user, has_auth_users
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
if settings.environment == "prod" and settings.mock_data:
    logger.warning("MOCK_DATA is enabled in prod; no real clinical data is used.")
if settings.auth_users.startswith("demo:demo"):
    logger.warning("AUTH_USERS is using the default demo credentials.")
if not has_auth_users():
    logger.error("AUTH_USERS is empty or invalid; all requests will be unauthorized.")

if settings.metrics_enabled:
    Instrumentator().instrument(app).expose(app, endpoint=settings.metrics_path, include_in_schema=False)

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


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in {"/_healthz", "/_readyz", "/login", "/logout"} or path.startswith("/static/") or path.startswith("/images/"):
            return await call_next(request)
        if path == settings.metrics_path and request.client:
            try:
                client_ip = ipaddress.ip_address(request.client.host)
                if client_ip.is_private or client_ip.is_loopback:
                    return await call_next(request)
            except ValueError:
                pass

        auth_user = get_session_user(request)
        if auth_user:
            request.state.auth_user = auth_user
            return await call_next(request)

        wants_json = "/api" in path or "application/json" in request.headers.get("accept", "")
        if wants_json:
            return JSONResponse({"detail": "Unauthorized"}, status_code=status.HTTP_401_UNAUTHORIZED)
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


app.add_middleware(AuthMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.auth_session_secret,
    session_cookie=settings.auth_session_cookie,
    max_age=settings.auth_session_max_age,
    same_site="lax",
    https_only=settings.environment == "prod",
)


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
