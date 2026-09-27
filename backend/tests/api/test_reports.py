import pytest
from uuid import UUID

@pytest.mark.asyncio
async def test_create_report_success(client):
    response = client.post("/api/v1/reports", json={
        "reported_phone": "+254700000000",
        "description": "Scam page"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_report_validation_error(client):
    response = client.post("/api/v1/reports", json={
        "description": "Forgot to include target info"
    })
    assert response.status_code == 422
    assert "At least one of target_url" in response.json()["error"]["message"]

@pytest.mark.asyncio
async def test_verify_payment_official(client):
    # Nairobi Sneaker Vault official till is 111111 in fixtures
    response = client.get("/api/v1/verify/payment?value=111111")
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "till"
    assert data["status"] == "official"
    assert data["merchant"]["business_name"] == "Nairobi Sneaker Vault"

@pytest.mark.asyncio
async def test_verify_payment_reported(client):
    # +254711111111 is reported and confirmed in fixtures
    response = client.get("/api/v1/verify/payment?value=0711111111")
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "phone"
    assert data["status"] == "reported"

@pytest.mark.asyncio
async def test_verify_payment_unknown(client):
    response = client.get("/api/v1/verify/payment?value=0700000000")
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "phone"
    assert data["status"] == "unknown"
