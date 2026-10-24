"""Merchant trust tiers and bio-code verification (TSK-044, docs/PRODUCT_V2.md section 5)."""

import asyncio
import json

from fastapi.testclient import TestClient

from app.core.repository import utcnow
from app.ingestion.fixtures import logos as L
from app.schemas.check import TargetProfileRecord

BASE = "/api/v1"


def onboard(
    client: TestClient, auth: dict[str, str], slug: str, handle: str, name: str = "Book Nook"
) -> dict:
    data = {
        "business_name": name,
        "slug": slug,
        "mpesa_type": "till",
        "mpesa_number": "778899",
        "phone_numbers": ["0701 234 567"],
        "handles": [{"platform": "instagram", "handle": handle}],
    }
    res = client.post(
        f"{BASE}/merchants",
        headers=auth,
        data={"data": json.dumps(data)},
        files={"logo": ("logo.png", L.png_bytes(L.hub_logo()), "image/png")},
    )
    assert res.status_code == 201, res.text
    return res.json()


def set_bio(client: TestClient, handle: str, bio: str, platform: str = "instagram") -> None:
    """Pretend the merchant edited their public bio (the offline demo reads stored profiles)."""
    repo = client.app.state.repo  # type: ignore[attr-defined]
    asyncio.run(
        repo.upsert_target_profile(
            TargetProfileRecord(
                platform=platform, handle=handle, bio=bio, fetched_via="opengraph", fetched_at=utcnow()
            )
        )
    )


def merchant_id(client: TestClient, slug: str) -> str:
    return client.get(f"{BASE}/merchants/{slug}").json()["id"]


def test_claimed_merchant_state_exposes_the_code_and_where_to_put_it(
    client: TestClient, auth: dict[str, str]
) -> None:
    body = onboard(client, auth, "book-nook", "booknook_ke")
    state = client.get(f"{BASE}/merchants/{body['id']}/verification", headers=auth).json()
    assert state["status"] == "claimed" and state["is_verified"] is False
    assert state["verification_code"] == body["verification_code"]
    assert state["handles_to_check"][0]["handle"] == "booknook_ke"
    assert body["verification_code"] in state["instructions"]
    assert client.get(f"{BASE}/merchants/{body['id']}/verification").status_code == 401


def test_code_missing_from_the_bio_is_422_and_changes_nothing(
    client: TestClient, auth: dict[str, str]
) -> None:
    body = onboard(client, auth, "book-nook", "booknook_ke")
    set_bio(client, "booknook_ke", "Books and stationery, Nairobi")
    res = client.post(f"{BASE}/merchants/{body['id']}/verification/check", headers=auth)
    assert res.status_code == 422 and res.json()["error"]["code"] == "VERIFICATION_CODE_NOT_FOUND"
    assert client.get(f"{BASE}/merchants/book-nook").json()["verification_status"] == "claimed"


def test_another_merchants_code_does_not_verify_you(client: TestClient, auth: dict[str, str]) -> None:
    mine = onboard(client, auth, "book-nook", "booknook_ke")
    other = onboard(client, auth, "paper-plus", "paperplus_ke", name="Paper Plus")
    set_bio(client, "booknook_ke", f"Books. {other['verification_code']}")
    res = client.post(f"{BASE}/merchants/{mine['id']}/verification/check", headers=auth)
    assert res.status_code == 422


def test_code_in_the_bio_verifies_and_makes_the_handle_official(
    client: TestClient, auth: dict[str, str]
) -> None:
    body = onboard(client, auth, "book-nook", "booknook_ke")
    before = client.post(f"{BASE}/check", json={"handle": "booknook_ke"}).json()
    assert before.get("verdict") != "official"            # unreachable (502) or scored, never official

    set_bio(client, "booknook_ke", f"Books & stationery | {body['verification_code'].upper()}")
    res = client.post(f"{BASE}/merchants/{body['id']}/verification/check", headers=auth)
    assert res.status_code == 200, res.text
    state = res.json()
    assert state["status"] == "verified" and state["is_verified"] is True
    assert state["found_on"] == "instagram:booknook_ke"
    assert state["verification_code"] is None and state["verified_at"]

    public = client.get(f"{BASE}/merchants/book-nook").json()
    assert public["verification_status"] == "verified" and public["verified_since"]
    assert client.post(f"{BASE}/check", json={"handle": "booknook_ke"}).json()["verdict"] == "official"
    again = client.post(f"{BASE}/merchants/{body['id']}/verification/check", headers=auth)
    assert again.status_code == 200 and again.json()["status"] == "verified"        # idempotent


def test_verified_merchant_can_now_be_impersonated_and_its_till_is_official(
    client: TestClient, auth: dict[str, str]
) -> None:
    body = onboard(client, auth, "book-nook", "booknook_ke")
    assert client.get(f"{BASE}/verify/payment", params={"value": "778899"}).json()["status"] == "unknown"

    set_bio(client, "booknook_ke", body["verification_code"])
    client.post(f"{BASE}/merchants/{body['id']}/verification/check", headers=auth)

    payment = client.get(f"{BASE}/verify/payment", params={"value": "778899"}).json()
    assert payment["status"] == "official" and payment["merchant"]["slug"] == "book-nook"
    clone = client.post(
        f"{BASE}/check",
        json={"handle": "booknook_ke_official", "manual": {"bio": "Lipa kwanza. Send money to 0798 555 444"}},
    ).json()
    assert clone["matched_merchant"]["slug"] == "book-nook"


def test_squatter_cannot_lock_the_real_owner_out_of_a_handle(
    client: TestClient, auth: dict[str, str]
) -> None:
    squatter = onboard(client, auth, "squat-shop", "booknook_ke", name="Squat Shop")
    real = onboard(client, auth, "book-nook", "booknook_ke")                       # same handle: allowed
    assert real["official_handles"][0]["handle"] == "booknook_ke"
    assert client.get(f"{BASE}/merchants/squat-shop").json()["official_handles"] == []

    set_bio(client, "booknook_ke", real["verification_code"])
    assert client.post(f"{BASE}/merchants/{real['id']}/verification/check", headers=auth).status_code == 200
    squat_check = client.post(f"{BASE}/merchants/{squatter['id']}/verification/check", headers=auth)
    assert squat_check.status_code == 422                                          # no handle left to prove


def test_a_verified_handle_cannot_be_claimed_by_someone_else(
    client: TestClient, auth: dict[str, str]
) -> None:
    body = onboard(client, auth, "book-nook", "booknook_ke")
    set_bio(client, "booknook_ke", body["verification_code"])
    client.post(f"{BASE}/merchants/{body['id']}/verification/check", headers=auth)
    res = client.post(
        f"{BASE}/merchants",
        headers=auth,
        data={"data": json.dumps({
            "business_name": "Copycat", "slug": "copycat",
            "handles": [{"platform": "instagram", "handle": "booknook_ke"}],
        })},
        files={"logo": ("logo.png", L.png_bytes(L.hub_logo()), "image/png")},
    )
    assert res.status_code == 409 and res.json()["error"]["code"] == "HANDLE_TAKEN"


def test_curated_seed_merchants_are_already_verified(client: TestClient, auth: dict[str, str]) -> None:
    public = client.get(f"{BASE}/merchants/nairobi-sneaker-vault").json()
    assert public["verification_status"] == "curated" and public["is_verified"] is True
    state = client.get(f"{BASE}/merchants/{public['id']}/verification", headers=auth).json()
    assert state["verification_code"] is None and state["handles_to_check"] == []
    assert client.post(
        f"{BASE}/merchants/{public['id']}/verification/check", headers=auth
    ).json()["status"] == "curated"


def test_unknown_merchant_is_404(client: TestClient, auth: dict[str, str]) -> None:
    ghost = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"{BASE}/merchants/{ghost}/verification", headers=auth).status_code == 404
    assert client.post(f"{BASE}/merchants/{ghost}/verification/check", headers=auth).status_code == 404
