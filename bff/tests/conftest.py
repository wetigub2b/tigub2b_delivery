"""
Pytest configuration for integration and unit tests.

Provides shared fixtures for:
- Database session management (async)
- Test database setup/teardown
- Common test data fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.core.config import settings


# Override database URL for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # In-memory SQLite for tests
# Or use a test MySQL database:
# TEST_DATABASE_URL = "mysql+asyncmy://user:pass@localhost:3306/tigu_b2b_test"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.

    This fixture is session-scoped to allow async fixtures
    to work properly across the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """
    Create async engine for test database.

    Uses in-memory SQLite for fast tests or a dedicated test MySQL database.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True to see SQL queries
        poolclass=NullPool,  # Don't pool connections for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide async database session for each test function.

    Each test gets a fresh session that is rolled back after the test,
    ensuring test isolation.
    """
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Rollback is automatic when exiting context
            # This ensures test isolation


@pytest.fixture(scope="function")
async def db_session(async_session: AsyncSession) -> AsyncSession:
    """
    Alias for async_session for backward compatibility.
    """
    return async_session


# Test data fixtures
@pytest.fixture
def sample_shop_id():
    """Sample merchant shop ID"""
    return 1


@pytest.fixture
def sample_user_id():
    """Sample user ID"""
    return 100


@pytest.fixture
def sample_warehouse_id():
    """Sample warehouse ID"""
    return 5


@pytest.fixture
def sample_driver_id():
    """Sample driver ID"""
    return 10


# Pytest markers configuration
def pytest_configure(config):
    """
    Register custom markers for test categorization.
    """
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "workflow: mark test as workflow integration test"
    )


# Asyncio marker
def pytest_collection_modifyitems(items):
    """
    Automatically mark async tests with asyncio marker.
    """
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
