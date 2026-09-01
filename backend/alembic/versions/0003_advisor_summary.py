"""add advisor_summary column to uploads

Revision ID: 0003_advisor_summary
Revises: 0002_provenance_sessions
Create Date: 2026-08-28 00:00:00.000000

File: backend/alembic/versions/0003_advisor_summary.py
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003_advisor_summary"
down_revision: str | None = "0002_provenance_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("uploads", sa.Column("advisor_summary", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("uploads", "advisor_summary")
