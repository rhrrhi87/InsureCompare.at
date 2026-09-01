"""provenance fields, sessions table, expanded clause types

Revision ID: 0002_provenance_sessions
Revises: 0001_initial
Create Date: 2026-08-27 00:00:00.000000

File: backend/alembic/versions/0002_provenance_sessions.py
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_provenance_sessions"
down_revision: str | None = "0001_initial"
branch_labels = None
depends_on = None

_NEW_CLAUSE_TYPES = (
    "deductible", "obligation", "territorial_scope", "duration", "optional_benefit",
)


def upgrade() -> None:
    # ---- Expand clause_type enum ----
    # PostgreSQL requires ALTER TYPE ... ADD VALUE to run outside the
    # surrounding migration's implicit transaction on older server versions;
    # AUTOCOMMIT keeps this migration portable across PG 12+.
    with op.get_context().autocommit_block():
        for value in _NEW_CLAUSE_TYPES:
            op.execute(f"ALTER TYPE clause_type ADD VALUE IF NOT EXISTS '{value}'")

    # ---- New extraction_method enum ----
    # create_type=False: the type is created explicitly on the next line;
    # without it, add_column() below would try to CREATE TYPE a second time
    # and fail with DuplicateObjectError (see the same fix/comment in
    # 0001_initial.py). Must be postgresql.ENUM, not the generic sa.Enum —
    # the generic type silently drops create_type on PG-dialect adaptation.
    extraction_method = postgresql.ENUM(
        "seed", "ocr_nlp", "manual", name="extraction_method", create_type=False
    )
    extraction_method.create(op.get_bind(), checkfirst=True)

    # ---- policies: provenance + retirement ----
    op.add_column("policies", sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "policies",
        sa.Column("is_demo_data", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
    )
    op.add_column("policies", sa.Column("document_title", sa.String(255), nullable=True))
    op.add_column("policies", sa.Column("document_type", sa.String(30), nullable=True))
    op.add_column("policies", sa.Column("source_url", sa.String(512), nullable=True))
    op.add_column("policies", sa.Column("source_organisation", sa.String(180), nullable=True))
    op.add_column("policies", sa.Column("retrieval_date", sa.Date(), nullable=True))
    op.add_column("policies", sa.Column("last_reviewed_date", sa.Date(), nullable=True))
    op.add_column(
        "policies",
        sa.Column("document_language", sa.String(5), nullable=False, server_default="de"),
    )

    # ---- clauses: upload linkage + language + extraction method ----
    # policy_id becomes optional: a clause now belongs to either a catalogue
    # policy OR a specific user upload, never both/neither.
    op.alter_column("clauses", "policy_id", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "clauses",
        sa.Column(
            "upload_id", sa.Integer(),
            sa.ForeignKey("uploads.id", ondelete="CASCADE"), nullable=True,
        ),
    )
    op.add_column(
        "clauses",
        sa.Column("document_language", sa.String(5), nullable=False, server_default="de"),
    )
    op.add_column(
        "clauses",
        sa.Column(
            "extraction_method", extraction_method, nullable=False, server_default="seed",
        ),
    )
    op.create_index("ix_clauses_upload_id", "clauses", ["upload_id"])

    # ---- sessions (refresh-token rotation / revocation) ----
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_refresh_token_hash", "sessions", ["refresh_token_hash"])


def downgrade() -> None:
    op.drop_index("ix_sessions_refresh_token_hash", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("ix_clauses_upload_id", table_name="clauses")
    op.drop_column("clauses", "extraction_method")
    op.drop_column("clauses", "document_language")
    op.drop_column("clauses", "upload_id")
    # Only safe if no upload-only (policy_id IS NULL) clauses exist yet.
    op.alter_column("clauses", "policy_id", existing_type=sa.Integer(), nullable=False)

    op.drop_column("policies", "document_language")
    op.drop_column("policies", "last_reviewed_date")
    op.drop_column("policies", "retrieval_date")
    op.drop_column("policies", "source_organisation")
    op.drop_column("policies", "source_url")
    op.drop_column("policies", "document_type")
    op.drop_column("policies", "document_title")
    op.drop_column("policies", "is_demo_data")
    op.drop_column("policies", "retired_at")

    sa.Enum(name="extraction_method").drop(op.get_bind(), checkfirst=True)

    # Note: PostgreSQL does not support removing values from an existing
    # enum type, so the clause_type additions from upgrade() are not
    # reversed here. Downgrading past this migration on a database that has
    # rows using the new clause types would violate the enum constraint if
    # those rows aren't cleaned up first.
