"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-02-14 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "sites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("patient_uid", sa.String(length=64), nullable=False),
        sa.Column("anon_label", sa.String(length=64), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=False),
        sa.Column("sex", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("patient_uid"),
    )

    op.create_table(
        "studies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("study_uid", sa.String(length=64), nullable=False),
        sa.Column("study_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("overall_risk", sa.String(length=32), nullable=False),
        sa.Column("nodule_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("study_uid"),
    )
    op.create_index("ix_study_date", "studies", ["study_date"])
    op.create_index("ix_status", "studies", ["status"])
    op.create_index("ix_overall_risk", "studies", ["overall_risk"])

    op.create_table(
        "series",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("study_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("series_uid", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("series_uid"),
    )

    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("series.id"), nullable=False),
        sa.Column("image_uid", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("thumbnail_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("image_uid"),
    )

    op.create_table(
        "qct_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("study_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("volume_total_mm3", sa.Float(), nullable=False),
        sa.Column("mean_diameter_mm", sa.Float(), nullable=False),
        sa.Column("vdt_days", sa.Integer(), nullable=False),
        sa.Column("overall_risk", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "qct_nodules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("study_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("nodule_uid", sa.String(length=64), nullable=False),
        sa.Column("location", sa.String(length=64), nullable=False),
        sa.Column("volume_mm3", sa.Float(), nullable=False),
        sa.Column("diameter_mm", sa.Float(), nullable=False),
        sa.Column("vdt_days", sa.Integer(), nullable=False),
        sa.Column("risk", sa.String(length=32), nullable=False),
        sa.Column("is_followup", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("nodule_uid"),
    )

    op.create_table(
        "qct_followups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("nodule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("qct_nodules.id"), nullable=False),
        sa.Column("prior_study_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("current_study_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("growth_percent", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "ingestion_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("study_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "access_audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("study_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("studies.id"), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_patient_uid", "patients", ["patient_uid"])


def downgrade() -> None:
    op.drop_index("ix_patient_uid", table_name="patients")
    op.drop_table("access_audits")
    op.drop_table("users")
    op.drop_table("ingestion_logs")
    op.drop_table("qct_followups")
    op.drop_table("qct_nodules")
    op.drop_table("qct_summaries")
    op.drop_table("images")
    op.drop_table("series")
    op.drop_index("ix_overall_risk", table_name="studies")
    op.drop_index("ix_status", table_name="studies")
    op.drop_index("ix_study_date", table_name="studies")
    op.drop_table("studies")
    op.drop_table("patients")
    op.drop_table("sites")
    op.drop_table("clients")
