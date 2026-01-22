"""Baseline schema with session blocks.

This migration resets the history for pre-production and creates all tables
from the current SQLAlchemy models in one step.
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import Column, String, inspect

# revision identifiers, used by Alembic.
revision = "0003_improve_child_reporting"
down_revision = "0002_initial_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables defined in SQLAlchemy models."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("children")}

    if "gender" not in existing_columns:
        op.add_column("children", Column("gender", String(100), nullable=True))


def downgrade() -> None:
    """Drop all tables defined in SQLAlchemy models."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("children")}

    if "gender" in existing_columns:
        op.drop_column("children", "gender")
