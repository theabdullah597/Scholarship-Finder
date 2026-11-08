from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_ok(
    client: AsyncClient, mock_db_session: AsyncMock, mock_redis: AsyncMock
) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"
    assert data["redis"] == "connected"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_check_db_failure(client: AsyncClient, mock_db_session: AsyncMock) -> None:
    mock_db_session.execute.side_effect = Exception("DB Connection Refused")
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["db"] == "disconnected"


@pytest.mark.asyncio
async def test_health_check_redis_failure(client: AsyncClient, mock_redis: AsyncMock) -> None:
    mock_redis.ping.side_effect = Exception("Redis connection timed out")
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"] == "disconnected"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "OpportunityAbroad" in data["message"]
    assert data["health"] == "/api/v1/health"
