from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import overview, scaffold, studies
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

app.include_router(overview.router)
app.include_router(studies.router)
app.include_router(scaffold.router)
