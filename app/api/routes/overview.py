from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_db
from app.schemas.overview import OverviewResponse
from app.services.provider import get_provider

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def overview_page(request: Request, db=Depends(get_db)):
    provider = get_provider()
    kpis = provider.get_overview_kpis(db)
    risk_breakdown = provider.get_risk_breakdown(db)
    volume_trend = provider.get_volume_trend(db)
    return templates.TemplateResponse(
        "overview.html",
        {
            "request": request,
            "kpis": kpis,
            "risk_breakdown": risk_breakdown,
            "volume_trend": volume_trend,
        },
    )


@router.get("/api/overview", response_model=OverviewResponse)
def overview_api(db=Depends(get_db)):
    provider = get_provider()
    return {
        "kpis": provider.get_overview_kpis(db),
        "risk_breakdown": provider.get_risk_breakdown(db),
        "volume_trend": provider.get_volume_trend(db),
    }
