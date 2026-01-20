import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure all SQLAlchemy models are imported/registered before create_all runs.
# This avoids missing tables due to import order (especially in worker/CLI contexts).
import app.models  # noqa: F401
from app.config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)


def _configure_sqlalchemy_logging() -> None:
    # If SQL echo is enabled, don't interfere with SQLAlchemy's engine logging.
    if settings.sqlalchemy_echo:
        return

    # Silence verbose SQL statement logging (common when `echo=True`).
    for logger_name in (
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


_configure_sqlalchemy_logging()

engine = create_async_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Add event listeners for slow query logging (only with sync engine events)
# Note: Async query logging would require custom instrumentation
_slow_query_threshold = settings.otel_slow_query_threshold_ms / 1000.0  # Convert to seconds


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ensure_blocks_exist(db: AsyncSession) -> None:
    """Ensure term and special blocks exist for current year + next year."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from app.models.session_block import SessionBlock

    tz = ZoneInfo("Pacific/Auckland")
    current_year = datetime.now(tz).year
    years_to_populate = [current_year, current_year + 1]

    for year in years_to_populate:
        # Check if blocks already exist for this year
        existing = await db.execute(select(SessionBlock).where(SessionBlock.year == year))
        if existing.scalars().first():
            continue  # Blocks already exist for this year

        # Create term blocks (1-4)
        for term_num in range(1, 5):
            block = SessionBlock(
                year=year,
                block_type=f"term_{term_num}",
                name=f"Term {term_num}",
                start_date=datetime(year, 1, 1, tzinfo=tz).date(),  # Placeholder
                end_date=datetime(year, 12, 31, tzinfo=tz).date(),  # Placeholder
            )
            db.add(block)

        # Create special block
        special = SessionBlock(
            year=year,
            block_type="special",
            name="Special Events",
            start_date=datetime(year, 1, 1, tzinfo=tz).date(),
            end_date=datetime(year, 12, 31, tzinfo=tz).date(),
            timezone="Pacific/Auckland",
        )
        db.add(special)

    await db.commit()


@asynccontextmanager
async def lifespan_db():
    """Create tables on startup (dev only - use migrations in prod)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure blocks exist for current + next year
    async with async_session_factory() as session:
        try:
            await ensure_blocks_exist(session)
        except Exception as e:
            logger.warning(f"Failed to ensure blocks exist: {e}")

    yield
    await engine.dispose()
