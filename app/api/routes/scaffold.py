from __future__ import annotations

from math import ceil
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.queries import (
    count_followups,
    count_ingestion_logs,
    get_followup_timeline,
    get_ingestion_logs,
)

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/followups", response_class=HTMLResponse)
def followups_page(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    per_page = max(1, min(per_page, 100))
    total = count_followups(db, search=q)
    total_pages = max(1, ceil(total / per_page))
    page = min(page, total_pages)
    offset = (page - 1) * per_page
    followups = get_followup_timeline(db, limit=per_page, offset=offset, search=q)
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


@router.get("/ingestion", response_class=HTMLResponse)
def ingestion_page(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    per_page = max(1, min(per_page, 100))
    total = count_ingestion_logs(db, search=q)
    total_pages = max(1, ceil(total / per_page))
    page = min(page, total_pages)
    offset = (page - 1) * per_page
    logs = get_ingestion_logs(db, limit=per_page, offset=offset, search=q)
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
