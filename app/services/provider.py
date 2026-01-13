from __future__ import annotations

import hashlib
import logging
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import queries


class DataProvider(Protocol):
    def get_overview_kpis(self, db: Session) -> dict[str, int]:
        ...

    def get_risk_breakdown(self, db: Session) -> list[dict[str, int]]:
        ...

    def get_volume_trend(self, db: Session) -> list[dict[str, float]]:
        ...

    def list_studies(
        self,
        db: Session,
        status: str | None = None,
        risk: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, object]]:
        ...

    def count_studies(
        self,
        db: Session,
        status: str | None = None,
        risk: str | None = None,
        search: str | None = None,
    ) -> int:
        ...

    def get_study_detail(self, db: Session, study_id: str) -> dict[str, object] | None:
        ...

    def get_followup_timeline(
        self,
        db: Session,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, object]]:
        ...

    def count_followups(self, db: Session, search: str | None = None) -> int:
        ...

    def get_ingestion_logs(
        self,
        db: Session,
        limit: int = 30,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, object]]:
        ...

    def count_ingestion_logs(self, db: Session, search: str | None = None) -> int:
        ...


def _mask_patient_id(patient_uid: str | None, anon_label: str | None) -> str:
    if settings.allow_phi:
        return patient_uid or anon_label or ""
    if anon_label:
        return anon_label
    if not patient_uid:
        return ""
    digest = hashlib.sha256(patient_uid.encode("utf-8")).hexdigest()[:8]
    return f"Anon-{digest}"


class MockProvider:
    def get_overview_kpis(self, db: Session) -> dict[str, int]:
        return queries.get_overview_kpis(db)

    def get_risk_breakdown(self, db: Session) -> list[dict[str, int]]:
        return queries.get_risk_breakdown(db)

    def get_volume_trend(self, db: Session) -> list[dict[str, float]]:
        return queries.get_volume_trend(db)

    def list_studies(
        self,
        db: Session,
        status: str | None = None,
        risk: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, object]]:
        studies = queries.list_studies(
            db, status=status, risk=risk, search=search, limit=limit, offset=offset
        )
        rows = []
        for study in studies:
            rows.append(
                {
                    "id": study.id,
                    "study_uid": study.study_uid,
                    "patient_uid": _mask_patient_id(
                        study.patient.patient_uid, study.patient.anon_label
                    ),
                    "study_date": study.study_date,
                    "status": study.status,
                    "overall_risk": study.overall_risk,
                    "nodule_count": study.nodule_count,
                }
            )
        return rows

    def count_studies(
        self,
        db: Session,
        status: str | None = None,
        risk: str | None = None,
        search: str | None = None,
    ) -> int:
        return queries.count_studies(db, status=status, risk=risk, search=search)

    def get_study_detail(self, db: Session, study_id: str) -> dict[str, object] | None:
        detail = queries.get_study_detail(db, study_id)
        if not detail:
            return None
        detail["patient_uid"] = _mask_patient_id(
            detail.get("patient_uid"), detail.get("anon_label")
        )
        return detail

    def get_followup_timeline(
        self,
        db: Session,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, object]]:
        timeline = queries.get_followup_timeline(db, limit=limit, offset=offset, search=search)
        for item in timeline:
            item["patient_uid"] = _mask_patient_id(
                item.get("patient_uid"), item.get("anon_label")
            )
        return timeline

    def count_followups(self, db: Session, search: str | None = None) -> int:
        return queries.count_followups(db, search=search)

    def get_ingestion_logs(
        self,
        db: Session,
        limit: int = 30,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, object]]:
        logs = queries.get_ingestion_logs(db, limit=limit, offset=offset, search=search)
        for log in logs:
            log["patient_uid"] = _mask_patient_id(
                log.get("patient_uid"), log.get("anon_label")
            )
        return logs

    def count_ingestion_logs(self, db: Session, search: str | None = None) -> int:
        return queries.count_ingestion_logs(db, search=search)


class OrthancProvider:
    def get_overview_kpis(self, db: Session) -> dict[str, int]:
        return {
            "total_patients": 0,
            "total_studies": 0,
            "total_nodules": 0,
            "high_risk": 0,
        }

    def get_risk_breakdown(self, db: Session) -> list[dict[str, int]]:
        return [{"label": risk, "value": 0} for risk in queries.RISK_ORDER]

    def get_volume_trend(self, db: Session) -> list[dict[str, float]]:
        return []

    def list_studies(
        self,
        db: Session,
        status: str | None = None,
        risk: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, object]]:
        return []

    def count_studies(
        self,
        db: Session,
        status: str | None = None,
        risk: str | None = None,
        search: str | None = None,
    ) -> int:
        return 0

    def get_study_detail(self, db: Session, study_id: str) -> dict[str, object] | None:
        return None

    def get_followup_timeline(
        self,
        db: Session,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, object]]:
        return []

    def count_followups(self, db: Session, search: str | None = None) -> int:
        return 0

    def get_ingestion_logs(
        self,
        db: Session,
        limit: int = 30,
        offset: int = 0,
        search: str | None = None,
    ) -> list[dict[str, object]]:
        return []

    def count_ingestion_logs(self, db: Session, search: str | None = None) -> int:
        return 0


def get_provider() -> DataProvider:
    global _mock_notice_emitted
    source = settings.data_source.lower()
    if source == "orthanc":
        if not _mock_notice_emitted:
            if settings.mock_data:
                logger.warning(
                    "DATA_SOURCE=orthanc is configured as MOCK; no real Orthanc integration is enabled."
                )
            else:
                logger.error(
                    "DATA_SOURCE=orthanc requires MOCK_DATA=true in this build; "
                    "no real Orthanc integration exists."
                )
            _mock_notice_emitted = True
        return OrthancProvider()
    if settings.mock_data and not _mock_notice_emitted:
        logger.info("MOCK_DATA is enabled; serving simulated data.")
        _mock_notice_emitted = True
    return MockProvider()
logger = logging.getLogger("app.provider")
_mock_notice_emitted = False
