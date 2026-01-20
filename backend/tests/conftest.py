from __future__ import annotations

import os
from typing import TYPE_CHECKING

# Define test schema name first
TEST_SCHEMA_NAME = "test_schema"

# Set test environment BEFORE any app imports (settings are cached on first import)
os.environ.update(
    {
        "SECRET_KEY": "secret-key",
        # Force deterministic database URL for tests regardless of host env.
        # Note: asyncpg uses server_settings, not options parameter
        "DATABASE_URL": "postgresql+asyncpg://sessions:changeme@localhost:5432/sessions",
        "DATABASE_ECHO": "false",
        "DATABASE_ECHO_POOL": "false",
        "SAQ_USE_SERVER_LIFESPAN": "False",
        "SAQ_WEB_ENABLED": "True",
        "SAQ_PROCESSES": "1",
        "SAQ_CONCURRENCY": "1",
        "VITE_PORT": "3006",
        "VITE_DEV_MODE": "True",
        "EMAIL_BACKEND": "memory",
        "LITESTAR_DEBUG": "True",
        # Disable auto-population of session blocks during tests
        "POPULATE_BLOCKS_ON_STARTUP": "False",
    }
)

# Now import app modules after environment is configured
import pytest
import pytest_asyncio
from app.models.base import Base

# from litestar_email import EmailConfig, EmailService, InMemoryBackend
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncEngine


pytest_plugins = [
    "tests.data_fixtures",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def anyio_backend_options() -> dict[str, bool]:
    """Prefer uvloop when available for AnyIO's asyncio backend."""
    try:
        import uvloop  # noqa: F401
    except ImportError:
        return {}
    return {"use_uvloop": True}


@pytest_asyncio.fixture(name="engine", scope="session")
async def fx_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create SQLAlchemy async engine for tests.

    Priority:
    - Use DATABASE_URL from environment if provided (e.g., CI with PostgreSQL service)
    - Otherwise, default to local PostgreSQL on localhost:5432/test_db

    Note: Tests are designed for PostgreSQL. Ensure a PostgreSQL instance is available
    when running locally by starting the DB (e.g., `docker compose up -d postgres`).
    """
    password = os.environ.get("POSTGRES_PASSWORD", "changeme")
    default_url = f"postgresql+asyncpg://sessions:{password}@localhost:5432/sessions"
    override_url = os.environ.get("TEST_DATABASE_URL")

    # Always use a deterministic test database URL unless explicitly overridden
    db_url = override_url or default_url
    os.environ["DATABASE_URL"] = str(db_url)

    engine = create_async_engine(
        db_url,
        echo=False,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": TEST_SCHEMA_NAME}},
    )

    yield engine

    await engine.dispose()


@pytest.fixture(name="sessionmaker", scope="session")
def fx_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessionmaker factory bound to test engine."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture(name="db_schema", scope="session")
async def fx_db_schema(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Create schema once per test session.

    Note: Schema is created once and not dropped until session ends.
    Individual tests use db_cleanup for per-test isolation.
    """
    metadata = Base.metadata
    schema_name = TEST_SCHEMA_NAME
    async with engine.begin() as conn:
        # Ensure a clean slate in case leftover objects exist from previous runs.
        # Dropping and recreating the schema removes any lingering composite types
        # that can survive table drops (e.g., pg_type_typname_nsp_index conflicts).
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name};"))
        await conn.execute(text(f"SET search_path TO {schema_name};"))
        await conn.run_sync(metadata.create_all)
        
        # Create database views required by the app
        # sessions_public view - public-safe projection of sessions
        await conn.execute(text("""
            CREATE OR REPLACE VIEW sessions_public AS
            SELECT 
                id, name, age_lower, age_upper, day_of_week, start_time, end_time,
                waitlist, capacity, what_to_bring, prerequisites, archived,
                session_location_id, year, session_type, created_at, updated_at
            FROM sessions
        """))
        
        # session_occurrences_public view
        await conn.execute(text("""
            CREATE OR REPLACE VIEW session_occurrences_public AS
            SELECT id, session_id, starts_at, ends_at, cancelled, cancellation_reason
            FROM session_occurrences
        """))
        
        # children_staff view
        await conn.execute(text("""
            CREATE OR REPLACE VIEW children_staff AS
            SELECT id, caregiver_id, name, date_of_birth, media_consent, 
                   medical_info, needs_devices, other_info
            FROM children
        """))
        
        # caregivers_staff view
        await conn.execute(text("""
            CREATE OR REPLACE VIEW caregivers_staff AS
            SELECT id, name, email, phone, email_verified
            FROM caregivers
        """))
        
    yield
    async with engine.begin() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;"))


@pytest_asyncio.fixture
async def db_cleanup(engine: AsyncEngine, db_schema: None) -> AsyncGenerator[None, None]:
    """Per-test database cleanup for isolation.

    Truncates all tables before each test to ensure clean state,
    and again after each test to avoid leakage across modules.
    """
    # Clean up before test
    metadata = Base.metadata
    async with engine.begin() as conn:
        for table in reversed(metadata.sorted_tables):
            await conn.execute(table.delete())

    yield

    # Clean up after test
    async with engine.begin() as conn:
        for table in reversed(metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def session(
    sessionmaker: async_sessionmaker[AsyncSession],
    db_cleanup: None,
) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests with cleanup.

    Uses sessionmaker pattern which properly handles greenlet context
    for async psycopg driver.
    """
    async with sessionmaker() as session:
        yield session


@pytest_asyncio.fixture(name="db_session")
async def fx_db_session(
    sessionmaker: async_sessionmaker[AsyncSession],
    db_cleanup: None,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession fixture named `db_session` for integration tests."""
    async with sessionmaker() as session:
        yield session


# -----------------------------------------------------------------------------
# App and client fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def app(engine: AsyncEngine, db_schema: None) -> Litestar:
    """Create Litestar app for testing.

    The app uses the same PostgreSQL database as the test session.
    Replaces the app's default engine with the test engine that uses test_schema.
    """
    from app.server.asgi import create_app
    import app.db
    
    # Replace the app's engine and session factory with test versions
    app.db.engine = engine
    app.db.async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    return create_app()


@pytest_asyncio.fixture
async def test_client(app: Litestar) -> "AsyncGenerator[\"AsyncTestClient\", None]":
    """Provide an AsyncTestClient bound to the Litestar app."""
    from litestar.testing import AsyncTestClient

    async with AsyncTestClient(app=app) as client:
        yield client


# -----------------------------------------------------------------------------
# Email fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def email_service():  # type: ignore[no-untyped-def]
    """Create EmailService instance for testing with in-memory backend."""
    # Email service not currently implemented
    return


@pytest.fixture
def email_outbox() -> list:
    """Get the email outbox and clear it before each test."""
    # InMemoryBackend.clear()
    # return InMemoryBackend.outbox
    return []
