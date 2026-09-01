"""SQLAlchemy declarative base with timestamp mixin.

File: backend/app/db/base.py
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import DateTime, Enum, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_E = TypeVar("_E", bound=enum.Enum)

# Naming convention guarantees deterministic constraint names across migrations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Project-wide declarative base."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def str_enum(enum_cls: type[_E], *, name: str, **kwargs: Any) -> Enum:
    """``Enum`` column bound to a ``(str, enum.Enum)`` class that stores the
    member's *value* (e.g. ``"car"``) rather than SQLAlchemy's default of
    the member's *name* (``"CAR"``).

    Every native PostgreSQL enum type in this project's migrations is
    created with the lowercase ``.value`` strings as its labels (matching
    the JSON API and the frontend). Without ``values_callable`` here,
    SQLAlchemy silently sends ``.name`` instead, which only fails once a
    real Postgres enum type enforces the mismatch — the SQLite-backed test
    suite never catches it because SQLite has no native enum type to
    validate against.
    """
    return Enum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj], **kwargs)


class TimestampMixin:
    """Adds created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
