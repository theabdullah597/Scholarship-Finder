"""Focused tests for Phase 7 API hardening."""

from unittest.mock import AsyncMock

from httpx import AsyncClient


async def test_security_headers_are_present(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert response.headers["X-Request-ID"]


async def test_request_id_is_preserved(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "test-request"})

    assert response.headers["X-Request-ID"] == "test-request"


async def test_auth_rate_limit_returns_429_when_quota_is_exhausted(
    client: AsyncClient, monkeypatch
) -> None:
    monkeypatch.setattr("app.main.allow_request", AsyncMock(return_value=(False, 0)))

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.com", "password": "Password123!"},
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
