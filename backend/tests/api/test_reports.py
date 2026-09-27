"""Community reports, /verify/payment and override O3 (TSK-022), plus stats (section 5.9)."""

from uuid import UUID

from fastapi.testclient import TestClient

from app.ingestion.mock_seeder import seed_id

NSV = str(seed_id("merchant", "nsv"))


def verify(client: TestClient, value: str) -> dict:
    response = client.get("/api/v1/verify/payment", params={"value": value})
    assert response.status_code == 200, response.text
    return response.json()


def test_official_numbers(client: TestClient) -> None:
    till = verify(client, "543210")
    assert till["status"] == "official" and till["kind"] == "till"
    assert till["merchant"]["slug"] == "nairobi-sneaker-vault"
    pochi = verify(client, "+254 700 111 222")
    assert pochi["status"] == "official" and pochi["display"] == "0700 111 222"  # official numbers are public
    assert verify(client, "400200")["merchant"]["slug"] == "kilimani-glow"


def test_reported_number_is_masked(client: TestClient) -> None:
    data = verify(client, "0798999111")
    assert data == {
        "kind": "phone",
        "normalized": "+254798999111",
        "display": "0798 *** 111",
        "status": "reported",
        "merchant": None,
        "report_count": 2,
        "linked_threats": 1,
    }


def test_wa_me_link_is_accepted(client: TestClient) -> None:
    assert verify(client, "wa.me/254798999111")["status"] == "reported"


def test_unknown_is_not_safe(client: TestClient) -> None:
    data = verify(client, "889900")  # the competitor's own till: not registered with Halisi
    assert data["status"] == "unknown" and data["report_count"] == 0


def test_invalid_value_is_422(client: TestClient) -> None:
    response = client.get("/api/v1/verify/payment", params={"value": "hello"})
    assert response.status_code == 422 and response.json()["error"]["code"] == "INVALID_INPUT"


def test_report_requires_a_target(client: TestClient) -> None:
    assert client.post("/api/v1/reports", json={"description": "scam"}).status_code == 422
    assert (
        client.post("/api/v1/reports", json={"target_handle": "x", "platform": "myspace"}).status_code == 422
    )


def test_pending_report_does_not_flip_status_but_confirmed_does_and_o3_applies(client: TestClient) -> None:
    number = "0745 111 999"
    created = client.post(
        "/api/v1/reports", json={"reported_phone": number, "description": "asked for deposit"}
    )
    assert created.status_code == 201 and created.json()["status"] == "pending"
    pending = verify(client, number)
    assert pending["status"] == "unknown" and pending["report_count"] == 1

    page = {"handle": "nairobisneakervault.ke", "manual": {"bio": f"Order on {number}"}}
    before = client.post("/api/v1/check", json=page).json()
    assert "COMMUNITY_REPORTED" not in {r["code"] for r in before["reasons"]}

    import asyncio

    repo = client.app.state.repo
    asyncio.run(
        repo.set_report_status(UUID(created.json()["id"]), "confirmed")
    )  # moderation (no endpoint yet)
    assert verify(client, number)["status"] == "reported"

    after = client.post("/api/v1/check", json=page).json()
    assert "COMMUNITY_REPORTED" in {r["code"] for r in after["reasons"]}
    assert after["score"] >= 85  # O3 floor
    assert after["verdict"] == "impersonation"


def test_global_stats_are_counts(client: TestClient) -> None:
    stats = client.get("/api/v1/stats").json()
    assert stats["pages_scanned"] == 12  # 9 seeded pages + 3 official checks
    assert stats["threats_detected"] == 6
    assert stats["merchants_protected"] == 3
    assert stats["impersonations_blocked_7d"] == 6
    assert stats["top_platforms"] == [{"platform": "instagram", "count": 6}]
    assert stats["active_threats"] is None


def test_merchant_stats_need_key(client: TestClient, auth: dict[str, str]) -> None:
    assert client.get(f"/api/v1/stats?merchant_id={NSV}").status_code == 401
    stats = client.get(f"/api/v1/stats?merchant_id={NSV}", headers=auth).json()
    assert stats["active_threats"] == 2 and stats["resolved"] == 0
    assert stats["customers_warned_estimate"] == 0  # seeded scans are not real consumer checks
    client.post("/api/v1/check", json={"handle": "nairobi_sneakervault_official_ke"})
    assert (
        client.get(f"/api/v1/stats?merchant_id={NSV}", headers=auth).json()["customers_warned_estimate"] == 1
    )
