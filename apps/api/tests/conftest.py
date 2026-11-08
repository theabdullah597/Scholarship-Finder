from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app


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
async def client(
    mock_db_session: AsyncMock, mock_redis: AsyncMock
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.api.v1.endpoints.health.get_redis_client", return_value=mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()
