"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-25 00:00:00.000000

File: backend/alembic/versions/0001_initial.py
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- Enums ----
    # create_type=False on every enum here: each type is created explicitly
    # by the loop below (with checkfirst=True); without create_type=False,
    # SQLAlchemy's create_table() DDL compiler tries to CREATE TYPE a second
    # time for every column that uses one of these objects and fails with
    # DuplicateObjectError against a real PostgreSQL server (this codepath
    # is never exercised by the test suite, which builds SQLite schemas
    # directly from the ORM models rather than replaying this migration).
    #
    # NOTE: create_type is a postgresql.ENUM-specific constructor argument —
    # the generic, cross-dialect sa.Enum(...) silently accepts and discards
    # it, and reverts to create_type=True when adapted to the PG dialect at
    # DDL-compile time. postgresql.ENUM must be used directly here for the
    # flag to actually take effect.
    user_role = postgresql.ENUM("user", "admin", name="user_role", create_type=False)
    product_line = postgresql.ENUM(
        "car", "household", "travel", "legal", name="product_line", create_type=False
    )
    risk_level = postgresql.ENUM("low", "medium", "high", name="risk_level", create_type=False)
    risk_tolerance = postgresql.ENUM(
        "low", "medium", "high", name="risk_tolerance", create_type=False
    )
    coverage_level = postgresql.ENUM(
        "basic", "standard", "comprehensive", name="coverage_level", create_type=False
    )
    deductible_pref = postgresql.ENUM(
        "low", "medium", "high", name="deductible_preference", create_type=False
    )
    upload_status = postgresql.ENUM(
        "queued", "processing", "ready", "failed", name="upload_status", create_type=False
    )
    clause_type = postgresql.ENUM(
        "coverage", "exclusion", "limit", "definition", "other",
        name="clause_type", create_type=False,
    )

    for enum in (user_role, product_line, risk_level, risk_tolerance,
                 coverage_level, deductible_pref, upload_status, clause_type):
        enum.create(op.get_bind(), checkfirst=True)

    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("full_name", sa.String(120), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ---- providers ----
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="AT"),
        sa.Column("logo_url", sa.String(512), nullable=True),
        sa.Column("rating_score", sa.Numeric(3, 1), nullable=False, server_default="8.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # ---- policies ----
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider_id", sa.Integer(),
                  sa.ForeignKey("providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("product_line", product_line, nullable=False),
        sa.Column("monthly_premium_eur", sa.Numeric(10, 2), nullable=False),
        sa.Column("annual_premium_eur", sa.Numeric(10, 2), nullable=False),
        sa.Column("deductible_eur", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("coverage_limit_eur", sa.Numeric(14, 2), nullable=False),
        sa.Column("risk_level", risk_level, nullable=False, server_default="medium"),
        sa.Column("coverage_items", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("additional_features", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("exclusions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_policies_provider_id", "policies", ["provider_id"])
    op.create_index("ix_policies_product_line", "policies", ["product_line"])

    # ---- clauses ----
    op.create_table(
        "clauses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.Integer(),
                  sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_type", clause_type, nullable=False),
        sa.Column("label", sa.String(180), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="1.0"),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_clauses_policy_id", "clauses", ["policy_id"])
    op.create_index("ix_clauses_clause_type", "clauses", ["clause_type"])

    # ---- risk_profiles ----
    op.create_table(
        "risk_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insurance_type", product_line, nullable=False, server_default="car"),
        sa.Column("monthly_budget_eur", sa.Numeric(8, 2), nullable=False, server_default="100.00"),
        sa.Column("risk_tolerance", risk_tolerance, nullable=False, server_default="medium"),
        sa.Column("coverage_level", coverage_level, nullable=False, server_default="standard"),
        sa.Column("deductible_preference", deductible_pref, nullable=False, server_default="medium"),
        sa.Column("household_size", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("property_value_eur", sa.Numeric(12, 2), nullable=True),
        sa.Column("required_coverages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("weights", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", name="uq_risk_profiles_user_id"),
    )
    op.create_index("ix_risk_profiles_user_id", "risk_profiles", ["user_id"])

    # ---- uploads ----
    op.create_table(
        "uploads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("status", upload_status, nullable=False, server_default="queued"),
        sa.Column("ocr_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("extracted", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_uploads_user_id", "uploads", ["user_id"])
    op.create_index("ix_uploads_sha256", "uploads", ["sha256"])
    op.create_index("ix_uploads_status", "uploads", ["status"])

    # ---- recommendations ----
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_line", sa.String(32), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("ranked_policies", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])

    # ---- audit_logs ----
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_email", sa.String(254), nullable=True),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(60), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    for table in (
        "audit_logs", "recommendations", "uploads", "risk_profiles",
        "clauses", "policies", "providers", "users",
    ):
        op.drop_table(table)

    for enum_name in (
        "clause_type", "upload_status", "deductible_preference", "coverage_level",
        "risk_tolerance", "risk_level", "product_line", "user_role",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
