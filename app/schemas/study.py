from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StudyListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    study_uid: str
    patient_uid: str
    study_date: date
    status: str
    overall_risk: str
    nodule_count: int


class NoduleItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nodule_uid: str
    location: str
    volume_mm3: float
    diameter_mm: float
    vdt_days: int
    risk: str
    is_followup: bool


class SummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    volume_total_mm3: float
    mean_diameter_mm: float
    vdt_days: int
    overall_risk: str
    notes: str | None = None


class StudyDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    study_uid: str
    study_date: date
    status: str
    overall_risk: str
    patient_uid: str
    anon_label: str
    image_path: str
    summary: SummaryItem
    nodules: list[NoduleItem]
