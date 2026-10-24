"""Typosquat watchlist endpoints (TSK-047, docs/PRODUCT_V2.md section 6)."""

from fastapi.testclient import TestClient

from app.ingestion.mock_seeder import seed_id

BASE = "/api/v1"
NSV = str(seed_id("merchant", "nsv"))
KG = str(seed_id("merchant", "kg"))


def test_watchlist_lists_likely_lookalikes_per_official_handle(
    client: TestClient, auth: dict[str, str]
) -> None:
    data = client.get(f"{BASE}/merchants/{NSV}/watchlist", headers=auth).json()
    assert {h["platform"] for h in data["handles"]} == {"instagram", "tiktok"}
    instagram = next(h for h in data["handles"] if h["platform"] == "instagram")
    assert instagram["handle"] == "nairobisneakervault"
    assert "nairobisneakervau1t" in instagram["variants"]
    assert "nairobisneakervault" not in instagram["variants"]
    assert client.get(f"{BASE}/merchants/{NSV}/watchlist").status_code == 401


def test_scan_finds_the_clones_that_exist_and_nothing_else(client: TestClient, auth: dict[str, str]) -> None:
    res = client.post(f"{BASE}/merchants/{NSV}/watchlist/scan", headers=auth)
    assert res.status_code == 200, res.text
    scan = res.json()
    found = {f["handle"] for f in scan["findings"]}
    assert found == {"nairobi_sneakervault_official_ke", "nairobisneakervau1t"}
    assert all(f["verdict"] == "impersonation" and f["threat_id"] for f in scan["findings"])
    assert scan["findings"] == sorted(scan["findings"], key=lambda f: -f["score"])
    assert scan["resolved"] == 2 and scan["variants_generated"] > 20 and scan["budget_exhausted"] is False
    assert "nairobisneakerhub" not in found                      # the honest competitor is never a finding


def test_scan_does_not_cross_merchants(client: TestClient, auth: dict[str, str]) -> None:
    scan = client.post(f"{BASE}/merchants/{KG}/watchlist/scan", headers=auth).json()
    assert {f["handle"] for f in scan["findings"]} == {"kilimaniglow_official_ke", "kiiimaniglow"}


def test_claimed_merchant_has_a_watchlist_but_nothing_to_find(
    client: TestClient, auth: dict[str, str]
) -> None:
    import json

    from app.ingestion.fixtures import logos as L

    body = {
        "business_name": "Book Nook",
        "slug": "book-nook",
        "handles": [{"platform": "instagram", "handle": "booknook_ke"}],
    }
    created = client.post(
        f"{BASE}/merchants",
        headers=auth,
        data={"data": json.dumps(body)},
        files={"logo": ("l.png", L.png_bytes(L.hub_logo()), "image/png")},
    ).json()
    watch = client.get(f"{BASE}/merchants/{created['id']}/watchlist", headers=auth).json()
    assert watch["handles"][0]["variants"]
    scan = client.post(f"{BASE}/merchants/{created['id']}/watchlist/scan", headers=auth).json()
    assert scan["findings"] == []


def test_unknown_merchant_is_404(client: TestClient, auth: dict[str, str]) -> None:
    ghost = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"{BASE}/merchants/{ghost}/watchlist", headers=auth).status_code == 404
    assert client.post(f"{BASE}/merchants/{ghost}/watchlist/scan", headers=auth).status_code == 404
