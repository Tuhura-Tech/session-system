from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class ExclusionDate(Base, UUIDPrimaryKey, TimestampMixin):
    """A date where term sessions do not run (public holiday, closure, etc)."""

    __tablename__ = "exclusion_dates"
    __table_args__ = (UniqueConstraint("year", "date", name="uq_exclusion_dates_year_date"),)

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    exclusion_date: Mapped[date] = mapped_column("date", Date, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
