from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    sites: Mapped[list["Site"]] = relationship(back_populates="client")


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)

    client: Mapped[Client] = relationship(back_populates="sites")
    patients: Mapped[list["Patient"]] = relationship(back_populates="site")
    studies: Mapped[list["Study"]] = relationship(back_populates="site")


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"))
    patient_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    anon_label: Mapped[str] = mapped_column(String(64), nullable=False)
    birth_year: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(16), nullable=False)

    site: Mapped[Site] = relationship(back_populates="patients")
    studies: Mapped[list["Study"]] = relationship(back_populates="patient")


class Study(Base, TimestampMixin):
    __tablename__ = "studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"))
    study_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    study_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    overall_risk: Mapped[str] = mapped_column(String(32), nullable=False)
    nodule_count: Mapped[int] = mapped_column(Integer, nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="studies")
    site: Mapped[Site] = relationship(back_populates="studies")
    series: Mapped[list["Series"]] = relationship(back_populates="study")
    summary: Mapped["QCTSummary"] = relationship(back_populates="study", uselist=False)
    nodules: Mapped[list["QCTNodule"]] = relationship(back_populates="study")
    followups: Mapped[list["QCTFollowup"]] = relationship(
        back_populates="current_study",
        foreign_keys="QCTFollowup.current_study_id",
    )
    ingestion_logs: Mapped[list["IngestionLog"]] = relationship(back_populates="study")
    access_audits: Mapped[list["AccessAudit"]] = relationship(back_populates="study")

    __table_args__ = (
        Index("ix_study_date", "study_date"),
        Index("ix_status", "status"),
        Index("ix_overall_risk", "overall_risk"),
    )


class Series(Base, TimestampMixin):
    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studies.id"))
    series_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)

    study: Mapped[Study] = relationship(back_populates="series")
    images: Mapped[list["Image"]] = relationship(back_populates="series")


class Image(Base, TimestampMixin):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("series.id"))
    image_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    thumbnail_path: Mapped[str] = mapped_column(String(255), nullable=True)

    series: Mapped[Series] = relationship(back_populates="images")


class QCTSummary(Base, TimestampMixin):
    __tablename__ = "qct_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studies.id"))
    volume_total_mm3: Mapped[float] = mapped_column(Float, nullable=False)
    mean_diameter_mm: Mapped[float] = mapped_column(Float, nullable=False)
    vdt_days: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_risk: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    study: Mapped[Study] = relationship(back_populates="summary")


class QCTNodule(Base, TimestampMixin):
    __tablename__ = "qct_nodules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studies.id"))
    nodule_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    location: Mapped[str] = mapped_column(String(64), nullable=False)
    volume_mm3: Mapped[float] = mapped_column(Float, nullable=False)
    diameter_mm: Mapped[float] = mapped_column(Float, nullable=False)
    vdt_days: Mapped[int] = mapped_column(Integer, nullable=False)
    risk: Mapped[str] = mapped_column(String(32), nullable=False)
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False)

    study: Mapped[Study] = relationship(back_populates="nodules")
    followups: Mapped[list["QCTFollowup"]] = relationship(back_populates="nodule")


class QCTFollowup(Base, TimestampMixin):
    __tablename__ = "qct_followups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nodule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("qct_nodules.id"))
    prior_study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studies.id"))
    current_study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studies.id"))
    growth_percent: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    nodule: Mapped[QCTNodule] = relationship(back_populates="followups")
    prior_study: Mapped[Study] = relationship(foreign_keys=[prior_study_id])
    current_study: Mapped[Study] = relationship(back_populates="followups", foreign_keys=[current_study_id])


class IngestionLog(Base, TimestampMixin):
    __tablename__ = "ingestion_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studies.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    study: Mapped[Study] = relationship(back_populates="ingestion_logs")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)

    access_audits: Mapped[list["AccessAudit"]] = relationship(back_populates="user")


class AccessAudit(Base, TimestampMixin):
    __tablename__ = "access_audits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("studies.id"))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship(back_populates="access_audits")
    study: Mapped[Study] = relationship(back_populates="access_audits")


Index("ix_patient_uid", Patient.patient_uid)
