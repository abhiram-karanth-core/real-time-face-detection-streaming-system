"""
Integration tests for the FastAPI endpoints.

These use httpx's AsyncClient against the app directly —
no real server or database needed (we mock the DB dependency).
"""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """/health must return 200 and {"status": "ok"}."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_roi_invalid_uuid():
    """/roi with a non-UUID session_id must return 422 Unprocessable Entity."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/roi?session_id=not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_roi_valid_session_empty():
    """/roi with a valid UUID that has no data should return an empty list."""
    session_id = str(uuid.uuid4())

    with patch("main.get_roi_by_session", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/roi?session_id={session_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["count"] == 0
    assert body["roi"] == []


@pytest.mark.asyncio
async def test_roi_returns_data():
    """/roi should return whatever the DB layer provides."""
    session_id = str(uuid.uuid4())
    fake_row = {
        "id": 1,
        "session_id": session_id,
        "frame_id": str(uuid.uuid4()),
        "x": 100, "y": 80, "width": 200, "height": 240,
        "confidence": 0.95,
        "detected_at": "2024-01-01T00:00:00+00:00",
    }

    with patch("main.get_roi_by_session", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [fake_row]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/roi?session_id={session_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["roi"][0]["x"] == 100
    assert body["roi"][0]["confidence"] == 0.95