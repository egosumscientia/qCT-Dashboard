from __future__ import annotations

from math import ceil
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import authenticate_credentials, clear_session_user, ensure_db_user, set_session_user
from app.services.provider import get_provider

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/followups", response_class=HTMLResponse, dependencies=[Depends(get_current_user)])
def followups_page(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    per_page = max(1, min(per_page, 100))
    provider = get_provider()
    total = provider.count_followups(db, search=q)
    total_pages = max(1, ceil(total / per_page))
    page = min(page, total_pages)
    offset = (page - 1) * per_page
    followups = provider.get_followup_timeline(db, limit=per_page, offset=offset, search=q)
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "base_query": urlencode({"per_page": per_page, "q": q} if q else {"per_page": per_page}),
    }
    return templates.TemplateResponse(
        "followups.html",
        {
            "request": request,
            "followups": followups,
            "pagination": pagination,
            "search_query": q or "",
        },
    )


@router.get("/ingestion", response_class=HTMLResponse, dependencies=[Depends(get_current_user)])
def ingestion_page(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    per_page = max(1, min(per_page, 100))
    provider = get_provider()
    total = provider.count_ingestion_logs(db, search=q)
    total_pages = max(1, ceil(total / per_page))
    page = min(page, total_pages)
    offset = (page - 1) * per_page
    logs = provider.get_ingestion_logs(db, limit=per_page, offset=offset, search=q)
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "base_query": urlencode({"per_page": per_page, "q": q} if q else {"per_page": per_page}),
    }
    return templates.TemplateResponse(
        "ingestion.html",
        {
            "request": request,
            "logs": logs,
            "pagination": pagination,
            "search_query": q or "",
        },
    )


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": error,
        },
    )


@router.post("/login", include_in_schema=False)
async def login_action(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = (form.get("username") or "").strip()
    password = (form.get("password") or "").strip()
    auth_user = authenticate_credentials(username, password)
    if not auth_user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Credenciales invalidas.",
            },
            status_code=401,
        )
    ensure_db_user(db, auth_user)
    set_session_user(request, auth_user)
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout", include_in_schema=False)
def logout(request: Request) -> RedirectResponse:
    clear_session_user(request)
    return RedirectResponse(url="/login", status_code=303)
