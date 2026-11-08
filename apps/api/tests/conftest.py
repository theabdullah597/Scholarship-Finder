from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Test SQLite in-memory database with async connection
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Create all schema tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
def mock_db_session() -> AsyncMock:
    mock = AsyncMock(spec=AsyncSession)
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_redis() -> AsyncMock:
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    return mock


@pytest.fixture
async def client(db_session: AsyncSession, mock_redis: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.api.v1.endpoints.health.get_redis_client", return_value=mock_redis), \
         patch("app.services.email._send_smtp") as mock_smtp:
        mock_smtp.return_value = None
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()
