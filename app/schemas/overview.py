from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OverviewKpi(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_patients: int
    total_studies: int
    total_nodules: int
    high_risk: int


class RiskBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    value: int


class VolumeTrendPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    value: float


class OverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kpis: OverviewKpi
    risk_breakdown: list[RiskBreakdown]
    volume_trend: list[VolumeTrendPoint]
