import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import is_public_url
import ipaddress
import socket

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_api_key_auth(client: AsyncClient):
    # Test valid key
    headers = {"X-Halisi-Key": "change-me-long-random"}
    res = await client.post("/api/v1/merchants", headers=headers)
    assert res.status_code != 401

    # Test invalid key
    headers = {"X-Halisi-Key": "invalid"}
    res = await client.post("/api/v1/merchants", headers=headers)
    assert res.status_code == 401
    
    # Test missing key
    res = await client.post("/api/v1/merchants")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_rate_limit(client: AsyncClient):
    # /check is limited to 10/minute
    payload = {"url": "https://instagram.com/test"}
    # Send 11 requests
    for i in range(10):
        res = await client.post("/api/v1/check", json=payload)
        assert res.status_code == 200

    # 11th should be 429
    res = await client.post("/api/v1/check", json=payload)
    assert res.status_code == 429
    assert "error" in res.json()

def test_is_public_url(monkeypatch):
    def mock_gethostbyname_ex(hostname):
        if hostname == "localhost":
            return hostname, [], ["127.0.0.1"]
        elif hostname == "private.test":
            return hostname, [], ["192.168.1.1"]
        elif hostname == "link-local.test":
            return hostname, [], ["169.254.169.254"]
        elif hostname == "public.test":
            return hostname, [], ["8.8.8.8"]
        elif hostname == "mixed.test":
            return hostname, [], ["8.8.8.8", "10.0.0.1"]
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr(socket, "gethostbyname_ex", mock_gethostbyname_ex)

    # Valid
    assert is_public_url("https://public.test") is True

    # Invalid scheme
    assert is_public_url("http://public.test") is False

    # Private
    assert is_public_url("https://localhost") is False
    assert is_public_url("https://private.test") is False
    assert is_public_url("https://link-local.test") is False
    assert is_public_url("https://mixed.test") is False
    assert is_public_url("https://unknown.test") is False
