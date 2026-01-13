from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    Image,
    IngestionLog,
    Patient,
    QCTFollowup,
    QCTNodule,
    QCTSummary,
    Site,
    Study,
)


RISK_ORDER = ["low", "medium", "high"]


def get_overview_kpis(db: Session) -> dict[str, int]:
    total_patients = db.scalar(select(func.count(Patient.id))) or 0
    total_studies = db.scalar(select(func.count(Study.id))) or 0
    total_nodules = db.scalar(select(func.count(QCTNodule.id))) or 0
    high_risk = db.scalar(select(func.count(Study.id)).where(Study.overall_risk == "high")) or 0
    return {
        "total_patients": total_patients,
        "total_studies": total_studies,
        "total_nodules": total_nodules,
        "high_risk": high_risk,
    }


def get_risk_breakdown(db: Session) -> list[dict[str, int]]:
    rows = db.execute(
        select(Study.overall_risk, func.count(Study.id)).group_by(Study.overall_risk)
    ).all()
    counts = {risk: count for risk, count in rows}
    return [{"label": risk, "value": counts.get(risk, 0)} for risk in RISK_ORDER]


def get_volume_trend(db: Session) -> list[dict[str, float]]:
    rows = (
        db.execute(
            select(Study.study_date, func.avg(QCTSummary.volume_total_mm3))
            .join(QCTSummary, QCTSummary.study_id == Study.id)
            .group_by(Study.study_date)
            .order_by(Study.study_date)
        )
        .all()
    )
    return [{"label": row[0].isoformat(), "value": float(row[1])} for row in rows]


def list_studies(
    db: Session,
    status: str | None = None,
    risk: str | None = None,
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Sequence[Study]:
    query = select(Study).order_by(Study.study_date.desc())
    if status:
        query = query.where(Study.status == status)
    if risk:
        query = query.where(Study.overall_risk == risk)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.join(Study.patient).where(
            or_(
                Study.study_uid.ilike(pattern),
                Patient.patient_uid.ilike(pattern),
                Patient.anon_label.ilike(pattern),
            )
        )
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return db.scalars(query).all()


def count_studies(
    db: Session,
    status: str | None = None,
    risk: str | None = None,
    search: str | None = None,
) -> int:
    query = select(func.count(Study.id))
    if status:
        query = query.where(Study.status == status)
    if risk:
        query = query.where(Study.overall_risk == risk)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.join(Study.patient).where(
            or_(
                Study.study_uid.ilike(pattern),
                Patient.patient_uid.ilike(pattern),
                Patient.anon_label.ilike(pattern),
            )
        )
    return int(db.scalar(query) or 0)


def get_study_detail(db: Session, study_id: str) -> dict[str, object] | None:
    study = db.get(Study, study_id)
    if not study:
        return None

    patient = study.patient
    image_path = (
        db.execute(
            select(Image.file_path)
            .join(Image.series)
            .where(Image.series.has(study_id=study.id))
            .limit(1)
        )
        .scalars()
        .first()
    )
    summary = study.summary
    nodules = list(study.nodules)

    return {
        "id": study.id,
        "study_uid": study.study_uid,
        "study_date": study.study_date,
        "status": study.status,
        "overall_risk": study.overall_risk,
        "nodule_count": study.nodule_count,
        "patient_uid": patient.patient_uid,
        "anon_label": patient.anon_label,
        "image_path": image_path or "",
        "summary": summary,
        "nodules": nodules,
    }


def risk_palette() -> dict[str, str]:
    return {
        "low": "#5cb85c",
        "medium": "#f0ad4e",
        "high": "#d9534f",
    }


def get_followup_timeline(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
) -> list[dict[str, object]]:
    prior_study = aliased(Study)
    current_study = aliased(Study)
    query = (
        select(
            QCTFollowup,
            QCTNodule,
            prior_study,
            current_study,
            Patient,
            Site,
        )
        .join(QCTFollowup.nodule)
        .join(prior_study, QCTFollowup.prior_study)
        .join(current_study, QCTFollowup.current_study)
        .join(Patient, current_study.patient)
        .join(Site, current_study.site)
        .order_by(current_study.study_date.desc())
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Patient.patient_uid.ilike(pattern),
                Patient.anon_label.ilike(pattern),
                QCTNodule.nodule_uid.ilike(pattern),
                current_study.study_uid.ilike(pattern),
                prior_study.study_uid.ilike(pattern),
            )
        )
    rows = db.execute(query.limit(limit).offset(offset)).all()
    timeline = []
    for followup, nodule, prior, current, patient, site in rows:
        timeline.append(
            {
                "id": str(followup.id),
                "nodule_uid": nodule.nodule_uid,
                "patient_uid": patient.patient_uid,
                "anon_label": patient.anon_label,
                "site_name": site.name,
                "prior_study_uid": prior.study_uid,
                "prior_date": prior.study_date,
                "current_study_uid": current.study_uid,
                "current_date": current.study_date,
                "current_study_id": str(current.id),
                "growth_percent": round(followup.growth_percent, 1),
                "status": followup.status,
                "risk": current.overall_risk,
            }
        )
    return timeline


def count_followups(db: Session, search: str | None = None) -> int:
    prior_study = aliased(Study)
    current_study = aliased(Study)
    query = (
        select(func.count(QCTFollowup.id))
        .join(QCTFollowup.nodule)
        .join(prior_study, QCTFollowup.prior_study)
        .join(current_study, QCTFollowup.current_study)
        .join(Patient, current_study.patient)
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Patient.patient_uid.ilike(pattern),
                Patient.anon_label.ilike(pattern),
                QCTNodule.nodule_uid.ilike(pattern),
                current_study.study_uid.ilike(pattern),
                prior_study.study_uid.ilike(pattern),
            )
        )
    return int(db.scalar(query) or 0)


def get_ingestion_logs(
    db: Session,
    limit: int = 30,
    offset: int = 0,
    search: str | None = None,
) -> list[dict[str, object]]:
    query = (
        select(IngestionLog, Study, Patient, Site)
        .join(IngestionLog.study)
        .join(Study.patient)
        .join(Study.site)
        .order_by(IngestionLog.started_at.desc())
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Patient.patient_uid.ilike(pattern),
                Patient.anon_label.ilike(pattern),
                Study.study_uid.ilike(pattern),
                IngestionLog.message.ilike(pattern),
            )
        )
    rows = db.execute(query.limit(limit).offset(offset)).all()
    logs = []
    for log, study, patient, site in rows:
        logs.append(
            {
                "id": str(log.id),
                "status": log.status,
                "message": log.message,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
                "study_uid": study.study_uid,
                "study_id": str(study.id),
                "patient_uid": patient.patient_uid,
                "anon_label": patient.anon_label,
                "site_name": site.name,
            }
        )
    return logs


def count_ingestion_logs(db: Session, search: str | None = None) -> int:
    query = (
        select(func.count(IngestionLog.id))
        .join(IngestionLog.study)
        .join(Study.patient)
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Patient.patient_uid.ilike(pattern),
                Patient.anon_label.ilike(pattern),
                Study.study_uid.ilike(pattern),
                IngestionLog.message.ilike(pattern),
            )
        )
    return int(db.scalar(query) or 0)
