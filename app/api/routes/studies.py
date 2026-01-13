from __future__ import annotations

from datetime import datetime
from math import ceil
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import AccessAudit, User
from app.schemas.study import StudyDetail, StudyListItem
from app.services.provider import get_provider

router = APIRouter(prefix="/studies", dependencies=[Depends(get_current_user)])

templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def studies_page(
    request: Request,
    status: str | None = Query(default=None),
    risk: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    provider = get_provider()
    total = provider.count_studies(db, status=status, risk=risk, search=q)
    total_pages = max(1, ceil(total / per_page)) if per_page else 1
    page = min(page, total_pages)
    offset = (page - 1) * per_page
    rows = provider.list_studies(
        db, status=status, risk=risk, search=q, limit=per_page, offset=offset
    )
    base_params = {"per_page": per_page}
    if status:
        base_params["status"] = status
    if risk:
        base_params["risk"] = risk
    if q:
        base_params["q"] = q
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "base_query": urlencode(base_params),
    }
    return templates.TemplateResponse(
        "studies.html",
        {
            "request": request,
            "studies": rows,
            "selected_status": status or "",
            "selected_risk": risk or "",
            "search_query": q or "",
            "pagination": pagination,
        },
    )


@router.get("/api", response_model=list[StudyListItem])
def studies_api(
    status: str | None = Query(default=None),
    risk: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * per_page
    provider = get_provider()
    studies = provider.list_studies(
        db, status=status, risk=risk, search=q, limit=per_page, offset=offset
    )
    return [
        StudyListItem(**study)
        for study in studies
    ]


@router.get("/{study_id}", response_class=HTMLResponse)
def study_detail_page(
    request: Request,
    study_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider = get_provider()
    detail = provider.get_study_detail(db, study_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Study not found")

    audit = AccessAudit(
        user_id=current_user.id,
        study_id=detail["id"],
        action="view",
        ip_address=request.client.host if request.client else "unknown",
        accessed_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()

    return templates.TemplateResponse(
        "study_detail.html",
        {
            "request": request,
            "study": detail,
        },
    )


@router.get("/{study_id}/api", response_model=StudyDetail)
def study_detail_api(study_id: str, db: Session = Depends(get_db)):
    provider = get_provider()
    detail = provider.get_study_detail(db, study_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Study not found")

    return detail
