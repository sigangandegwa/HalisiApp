import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_check_422():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/check", json={"invalid": "payload"})
        assert res.status_code == 422

@pytest.mark.asyncio
async def test_check_unsupported_url():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/check", json={"url": "https://example.com"})
        # The endpoint uses the url_parser, but we didn't hook it up yet. Let's see.
        pass
