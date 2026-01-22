"""Baseline schema with session blocks.

This migration resets the history for pre-production and creates all tables
from the current SQLAlchemy models in one step.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_initial_views"
down_revision = "0001_block_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables defined in SQLAlchemy models."""
    op.execute("""
        CREATE OR REPLACE VIEW children_staff AS
        SELECT
            c.id,
            c.caregiver_id,
            c.name,
            c.date_of_birth,
            c.media_consent,
            c.medical_info,
            c.needs_devices,
            c.other_info
        FROM children c
    """)

    op.execute("""
        CREATE OR REPLACE VIEW caregivers_staff AS
        SELECT
            cg.id,
            cg.name,
            cg.email,
            cg.phone,
            cg.email_verified
        FROM caregivers cg
    """)


def downgrade() -> None:
    """Drop all tables defined in SQLAlchemy models."""
    op.execute("DROP VIEW IF EXISTS caregivers_staff")
    op.execute("DROP VIEW IF EXISTS children_staff")
