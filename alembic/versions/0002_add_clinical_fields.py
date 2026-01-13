"""add_clinical_fields

Revision ID: 0002_add_clinical_fields
Revises: 0001_initial
Create Date: 2026-01-13 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_add_clinical_fields'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('qct_summaries', sa.Column('lung_rads', sa.String(length=10), nullable=True))
    op.add_column('qct_summaries', sa.Column('algo_version', sa.String(length=32), nullable=True))
    op.add_column('qct_nodules', sa.Column('texture', sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column('qct_nodules', 'texture')
    op.drop_column('qct_summaries', 'algo_version')
    op.drop_column('qct_summaries', 'lung_rads')
