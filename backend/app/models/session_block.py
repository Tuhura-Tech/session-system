from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.session_block_link import SessionBlockLink
    from app.models.session_occurrence import SessionOccurrence


class SessionBlockType(enum.Enum):
    """Standard session block types - always 5 per year."""

    TERM_1 = "term_1"
    TERM_2 = "term_2"
    TERM_3 = "term_3"
    TERM_4 = "term_4"
    SPECIAL = "special"


class SessionBlock(Base, UUIDPrimaryKey, TimestampMixin):
    """A block (term or special) with a defined date range per year.

    There are always exactly 5 possible blocks per year:
    - Term 1, 2, 3, 4 (variable dates per year)
    - Special (always Jan 1 - Dec 31)

    Sessions link to blocks via SessionBlockLink.
    Occurrences belong to blocks via block_id.
    """

    __tablename__ = "session_blocks"

    __table_args__ = (UniqueConstraint("year", "block_type", name="uq_session_blocks_year_type"),)

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    block_type: Mapped[SessionBlockType] = mapped_column(String(20), nullable=False, index=True)

    # Display name (e.g., "Term 1", "Summer Special")
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Date range for this block
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Timezone for consistency
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Pacific/Auckland")

    # Relationships
    session_block_links: Mapped[list[SessionBlockLink]] = relationship(
        "SessionBlockLink", back_populates="block", cascade="all, delete-orphan"
    )

    occurrences: Mapped[list[SessionOccurrence]] = relationship("SessionOccurrence", back_populates="block")

    def __repr__(self) -> str:
        return f"SessionBlock(year={self.year}, type={self.block_type.value}, name={self.name!r})"
