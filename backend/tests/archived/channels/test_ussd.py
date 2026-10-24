"""Unit tests for Africa's Talking USSD channel (TSK-036)."""

import pytest
from fastapi.testclient import TestClient

from app.archived.channels.ussd import (
    ABOUT_TEXT,
    INVALID_CHOICE,
    INVALID_NUMBER,
    REPORT_PROMPT,
    VERIFY_PROMPT,
    WELCOME_MENU,
    handle_ussd,
)
from app.core.repository import MemoryRepository


@pytest.mark.asyncio
async def test_ussd_level_0_welcome_menu(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    resp = await handle_ussd(text="", phone_number="+254712345678", repo=repo)
    assert resp == WELCOME_MENU
    assert resp.startswith("CON ")


@pytest.mark.asyncio
async def test_ussd_option_1_prompt(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    resp = await handle_ussd(text="1", phone_number="+254712345678", repo=repo)
    assert resp == VERIFY_PROMPT
    assert resp.startswith("CON ")


@pytest.mark.asyncio
async def test_ussd_option_1_official_till(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    # 543210 is seeded official till for Nairobi Sneaker Vault
    resp = await handle_ussd(text="1*543210", phone_number="+254712345678", repo=repo)
    assert resp.startswith("END ")
    assert "VERIFIED OFFICIAL" in resp
    assert "Nairobi Sneaker Vault" in resp
    assert "Safe to pay." in resp


@pytest.mark.asyncio
async def test_ussd_option_1_official_phone(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    # +254712345678 is seeded official phone for Nairobi Sneaker Vault
    resp = await handle_ussd(text="1*0712345678", phone_number="+254712345678", repo=repo)
    assert resp.startswith("END ")
    assert "VERIFIED OFFICIAL" in resp
    assert "Nairobi Sneaker Vault" in resp



@pytest.mark.asyncio
async def test_ussd_option_1_reported_number(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    # 0798999111 is a seeded reported scam phone number
    resp = await handle_ussd(text="1*0798999111", phone_number="+254712345678", repo=repo)
    assert resp.startswith("END ")
    assert "ONYO! REPORTED SCAM" in resp
    assert "DO NOT SEND MONEY." in resp


@pytest.mark.asyncio
async def test_ussd_option_1_unknown_number(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    # 889900 is unverified/unknown till
    resp = await handle_ussd(text="1*889900", phone_number="+254712345678", repo=repo)
    assert resp.startswith("END ")
    assert "UNKNOWN NUMBER" in resp
    assert "Not registered with verified merchants." in resp


@pytest.mark.asyncio
async def test_ussd_option_1_invalid_input(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    resp = await handle_ussd(text="1*not_a_valid_number", phone_number="+254712345678", repo=repo)
    assert resp == INVALID_NUMBER
    assert resp.startswith("END ")


@pytest.mark.asyncio
async def test_ussd_option_2_report_prompt(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    resp = await handle_ussd(text="2", phone_number="+254712345678", repo=repo)
    assert resp == REPORT_PROMPT
    assert resp.startswith("CON ")


@pytest.mark.asyncio
async def test_ussd_option_2_submit_report(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    reported_num = "0711999888"
    resp = await handle_ussd(text=f"2*{reported_num}", phone_number="+254712345678", repo=repo)
    assert resp.startswith("END ")
    assert f"Asante! Scam report received for {reported_num}." in resp
    assert "Halisi team is investigating." in resp


@pytest.mark.asyncio
async def test_ussd_option_3_about(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    resp = await handle_ussd(text="3", phone_number="+254712345678", repo=repo)
    assert resp == ABOUT_TEXT
    assert resp.startswith("END ")
    assert "Visit halisi.co.ke" in resp


@pytest.mark.asyncio
async def test_ussd_invalid_menu_choice(client: TestClient) -> None:
    repo: MemoryRepository = client.app.state.repo
    resp = await handle_ussd(text="9", phone_number="+254712345678", repo=repo)
    assert resp == INVALID_CHOICE
    assert resp.startswith("END ")


def test_ussd_endpoint_http_flow(client: TestClient) -> None:
    # 1. Initial dial (Level 0)
    res0 = client.post(
        "/api/v1/channels/ussd",
        data={
            "sessionId": "ATUid_test_session_1",
            "serviceCode": "*384*123#",
            "phoneNumber": "+254712345678",
            "text": "",
        },
    )
    assert res0.status_code == 200
    assert res0.headers["content-type"].startswith("text/plain")
    assert res0.text.startswith("CON Karibu Halisi!")

    # 2. Select option 1 (Level 1)
    res1 = client.post(
        "/api/v1/channels/ussd",
        data={
            "sessionId": "ATUid_test_session_1",
            "serviceCode": "*384*123#",
            "phoneNumber": "+254712345678",
            "text": "1",
        },
    )
    assert res1.status_code == 200
    assert res1.text.startswith("CON Enter Till, Paybill or Phone number to check:")

    # 3. Enter official till 543210 (Level 2)
    res2 = client.post(
        "/api/v1/channels/ussd",
        data={
            "sessionId": "ATUid_test_session_1",
            "serviceCode": "*384*123#",
            "phoneNumber": "+254712345678",
            "text": "1*543210",
        },
    )
    assert res2.status_code == 200
    assert res2.text.startswith("END Halisi: VERIFIED OFFICIAL.")
    assert "Nairobi Sneaker Vault" in res2.text

    # 4. Check reported scam number
    res_scam = client.post(
        "/api/v1/channels/ussd",
        data={
            "sessionId": "ATUid_test_session_2",
            "serviceCode": "*384*123#",
            "phoneNumber": "+254712345678",
            "text": "1*0798999111",
        },
    )
    assert res_scam.status_code == 200
    assert res_scam.text.startswith("END Halisi: ONYO! REPORTED SCAM.")

    # 5. Report scam number via option 2
    res_report = client.post(
        "/api/v1/channels/ussd",
        data={
            "sessionId": "ATUid_test_session_3",
            "serviceCode": "*384*123#",
            "phoneNumber": "+254712345678",
            "text": "2*0799000111",
        },
    )
    assert res_report.status_code == 200
    assert "Asante! Scam report received for 0799000111." in res_report.text

    # 6. About Halisi option 3
    res_about = client.post(
        "/api/v1/channels/ussd",
        data={
            "sessionId": "ATUid_test_session_4",
            "serviceCode": "*384*123#",
            "phoneNumber": "+254712345678",
            "text": "3",
        },
    )
    assert res_about.status_code == 200
    assert res_about.text.startswith("END Halisi protects Kenyan consumers")


def test_ussd_endpoint_snake_case_parameters(client: TestClient) -> None:
    res = client.post(
        "/api/v1/channels/ussd",
        data={
            "session_id": "ATUid_alt_1",
            "service_code": "*384#",
            "phone_number": "+254712345678",
            "text": "3",
        },
    )
    assert res.status_code == 200
    assert res.text == ABOUT_TEXT