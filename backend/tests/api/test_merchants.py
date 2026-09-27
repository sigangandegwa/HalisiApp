"""Merchant endpoints: public profile, onboarding, threat feed and detail (sections 5.4-5.6)."""

import json

from fastapi.testclient import TestClient

from app.ingestion.fixtures import logos as L
from app.ingestion.mock_seeder import seed_id

NSV = str(seed_id("merchant", "nsv"))


def test_public_profile(client: TestClient) -> None:
    data = client.get("/api/v1/merchants/pwani-threads").json()
    assert data["business_name"] == "Pwani Threads"
    assert data["payment"] == {"type": "pochi", "number": "+254700111222", "account_name": "PWANI THREADS"}
    assert data["is_verified"] is True and data["verified_since"]
    assert {h["platform"] for h in data["official_handles"]} == {"instagram", "tiktok"}
    assert "logo_phash" not in data and "phone_numbers" not in data
    assert client.get("/api/v1/merchants/no-such-shop").status_code == 404


def test_seeded_payment_types_follow_the_spec(client: TestClient) -> None:
    types = {
        slug: client.get(f"/api/v1/merchants/{slug}").json()["payment"]["type"]
        for slug in ("nairobi-sneaker-vault", "kilimani-glow", "pwani-threads")
    }
    assert types == {"nairobi-sneaker-vault": "till", "kilimani-glow": "paybill", "pwani-threads": "pochi"}


def test_threat_feed_is_sorted_and_excludes_the_competitor(client: TestClient, auth: dict[str, str]) -> None:
    feed = client.get(f"/api/v1/merchants/{NSV}/threats", headers=auth).json()
    handles = [t["target_handle"] for t in feed]
    assert handles == ["nairobi_sneakervault_official_ke", "nairobisneakervau1t"]
    scores = [t["composite_score"] for t in feed]
    assert scores == sorted(scores, reverse=True)
    assert all(t["verdict"] == "impersonation" and t["status"] == "detected" for t in feed)
    assert feed[0]["top_reason"]["severity"] == "high"
    assert client.get(f"/api/v1/merchants/{NSV}/threats?status=resolved", headers=auth).json() == []
    assert client.get(f"/api/v1/merchants/{NSV}/threats?status=bogus", headers=auth).status_code == 422


def test_threat_detail_is_unmasked_for_the_merchant(client: TestClient, auth: dict[str, str]) -> None:
    feed = client.get(f"/api/v1/merchants/{NSV}/threats", headers=auth).json()
    detail = client.get(f"/api/v1/threats/{feed[0]['id']}", headers=auth).json()
    assert detail["extracted_phones"] == ["+254798999111"]
    assert detail["status"] == "detected" and detail["status_history"][0]["status"] == "detected"
    assert detail["verdict"] == "impersonation" and detail["score"] >= 90
    assert (
        detail["scan_id"]
        and detail["dimensions"]
        and detail["matched_merchant"]["slug"] == "nairobi-sneaker-vault"
    )
    assert detail["playbooks_generated"] == []


def test_patch_status_validates(client: TestClient, auth: dict[str, str]) -> None:
    feed = client.get(f"/api/v1/merchants/{NSV}/threats", headers=auth).json()
    ok = client.patch(f"/api/v1/threats/{feed[1]['id']}", json={"status": "takedown_filed"}, headers=auth)
    assert ok.status_code == 200 and ok.json()["status"] == "takedown_filed"
    bad = client.patch(f"/api/v1/threats/{feed[1]['id']}", json={"status": "deleted"}, headers=auth)
    assert bad.status_code == 422


def _onboard(client: TestClient, auth: dict[str, str], **overrides: object):
    data = {
        "business_name": "Eastlands Book Nook",
        "slug": "eastlands-book-nook",
        "category": "Books",
        "mpesa_type": "till",
        "mpesa_number": "778899",
        "mpesa_account_name": "EASTLANDS BOOK NOOK",
        "phone_numbers": ["0701 234 567"],
        "handles": [{"platform": "instagram", "handle": "@EastlandsBookNook"}],
    }
    data.update(overrides)
    logo = L.png_bytes(L.hub_logo())
    return client.post(
        "/api/v1/merchants",
        headers=auth,
        data={"data": json.dumps(data)},
        files={"logo": ("logo.png", logo, "image/png")},
    )


def test_onboarding_computes_hashes_and_makes_the_handle_official(
    client: TestClient, auth: dict[str, str]
) -> None:
    created = _onboard(client, auth)
    assert created.status_code == 201, created.text
    body = created.json()
    assert len(body["logo_phash"]) == 16 and len(body["logo_dhash"]) == 16 and body["clip"] is False
    assert body["official_handles"][0]["handle"] == "eastlandsbooknook"
    assert body["logo_url"].startswith("/media/")
    assert client.get(body["logo_url"]).status_code == 200
    check = client.post("/api/v1/check", json={"handle": "eastlandsbooknook"}).json()
    assert check["verdict"] == "official"
    clone = client.post(
        "/api/v1/check",
        json={"handle": "eastlandsbooknook_official", "manual": {"bio": "Send money to 0798 555 444"}},
    ).json()
    assert clone["matched_merchant"]["slug"] == "eastlands-book-nook"


def test_onboarding_rejects_bad_input(client: TestClient, auth: dict[str, str]) -> None:
    assert _onboard(client, auth, slug="Bad Slug!").status_code == 422
    dup = _onboard(client, auth, slug="nairobi-sneaker-vault")
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "SLUG_TAKEN"
    taken = _onboard(client, auth, handles=[{"platform": "instagram", "handle": "kilimaniglow"}])
    assert taken.status_code == 409 and taken.json()["error"]["code"] == "HANDLE_TAKEN"
    not_image = client.post(
        "/api/v1/merchants",
        headers=auth,
        data={"data": json.dumps({"business_name": "X Shop", "slug": "x-shop"})},
        files={"logo": ("l.png", b"not an image", "image/png")},
    )
    assert not_image.status_code == 422 and not_image.json()["error"]["code"] == "INVALID_IMAGE"
    wrong_type = client.post(
        "/api/v1/merchants",
        headers=auth,
        data={"data": json.dumps({"business_name": "X Shop", "slug": "x-shop"})},
        files={"logo": ("l.gif", b"GIF89a", "image/gif")},
    )
    assert wrong_type.status_code == 422
