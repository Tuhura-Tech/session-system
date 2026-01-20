"""Add SessionBlock and SessionBlockLink tables.

Revision ID: add_session_blocks_001
Revises:
Create Date: 2026-01-17 02:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_session_blocks_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create session_blocks table
    op.create_table(
        "session_blocks",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Pacific/Auckland"),
        sa.CheckConstraint(
            "(block_type = 'special' AND start_date = '01-01' AND end_date = '12-31') OR (block_type != 'special')",
            name="ck_session_blocks_special_dates",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "block_type", name="uq_session_blocks_year_type"),
    )
    op.create_index("ix_session_blocks_year", "session_blocks", ["year"])
    op.create_index("ix_session_blocks_block_type", "session_blocks", ["block_type"])

    # Create session_block_links table
    op.create_table(
        "session_block_links",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(), nullable=False),
        sa.Column("block_id", postgresql.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["block_id"], ["session_blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "block_id", name="uq_session_block_links_session_block"),
    )
    op.create_index("ix_session_block_links_session_id", "session_block_links", ["session_id"])
    op.create_index("ix_session_block_links_block_id", "session_block_links", ["block_id"])

    # Add block_id to session_occurrences
    op.add_column("session_occurrences", sa.Column("block_id", postgresql.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_session_occurrences_block_id",
        "session_occurrences",
        "session_blocks",
        ["block_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_session_occurrences_block_id", "session_occurrences", ["block_id"])


def downgrade() -> None:
    op.drop_index("ix_session_occurrences_block_id", table_name="session_occurrences")
    op.drop_constraint("fk_session_occurrences_block_id", "session_occurrences", type_="foreignkey")
    op.drop_column("session_occurrences", "block_id")

    op.drop_index("ix_session_block_links_block_id", table_name="session_block_links")
    op.drop_index("ix_session_block_links_session_id", table_name="session_block_links")
    op.drop_table("session_block_links")

    op.drop_index("ix_session_blocks_block_type", table_name="session_blocks")
    op.drop_index("ix_session_blocks_year", table_name="session_blocks")
    op.drop_table("session_blocks")
