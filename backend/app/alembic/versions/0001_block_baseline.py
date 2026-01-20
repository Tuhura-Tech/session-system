"""Baseline schema with session blocks.

This migration resets the history for pre-production and creates all tables
from the current SQLAlchemy models in one step.
"""

from __future__ import annotations

from alembic import op

from app.models import Base

# revision identifiers, used by Alembic.
revision = "0001_block_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables defined in SQLAlchemy models."""
    bind = op.get_bind()
    Base.metadata.create_all(bind)

    # Create views for public endpoints
    op.execute("""
        CREATE VIEW sessions_public AS
        SELECT
            s.id,
            s.name,
            s.age_lower,
            s.age_upper,
            s.day_of_week,
            s.start_time,
            s.end_time,
            s.year,
            s.session_type,
            s.what_to_bring,
            s.prerequisites,
            s.waitlist,
            l.id AS location_id,
            l.name AS location_name,
            l.address AS location_address,
            l.region AS location_region,
            l.lat AS location_lat,
            l.lng AS location_lng,
            l.instructions AS location_instructions
        FROM sessions s
        JOIN session_locations l ON l.id = s.session_location_id
        WHERE COALESCE(s.archived, false) = false
    """)

    op.execute("""
        CREATE VIEW session_occurrences_public AS
        SELECT
            so.id,
            so.session_id,
            so.starts_at,
            so.ends_at,
            so.cancelled,
            so.cancellation_reason
        FROM session_occurrences so
    """)


def downgrade() -> None:
    """Drop all tables defined in SQLAlchemy models."""
    bind = op.get_bind()
    op.execute("DROP VIEW IF EXISTS session_occurrences_public")
    op.execute("DROP VIEW IF EXISTS sessions_public")
    Base.metadata.drop_all(bind)
