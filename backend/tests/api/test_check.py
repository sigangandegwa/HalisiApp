"""POST /check and GET /check/{scan_id} (docs/BACKEND.md sections 5.2, 12). DEMO_MODE, no network."""

import base64

from fastapi.testclient import TestClient

from app.ingestion.fixtures import logos as L


def check(client: TestClient, **body: object) -> dict:
    response = client.post("/api/v1/check", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def test_blatant_clone_is_impersonation_through_the_real_engine(client: TestClient) -> None:
    data = check(client, url="https://www.instagram.com/nairobi_sneakervault_official_ke/?igsh=abc123")
    assert data["verdict"] == "impersonation"
    assert data["score"] >= 90
    assert data["confidence"] == 1.0
    assert data["matched_merchant"]["slug"] == "nairobi-sneaker-vault"
    assert data["target"]["handle"] == "nairobi_sneakervault_official_ke"
    assert data["target"]["url"] == "https://instagram.com/nairobi_sneakervault_official_ke"
    assert data["target"]["fetched_via"] == "seed"
    assert [d["key"] for d in data["dimensions"]] == ["visual", "identity", "payment", "language", "account"]
    assert {"LOGO_COPY", "HANDLE_LOOKALIKE", "POCHI_REQUEST", "COMMUNITY_REPORTED"} <= {
        r["code"] for r in data["reasons"]
    }
    assert data["hashes"]["hamming_distance"] <= 4
    assert data["safe_action"]["text"].startswith("Pay only via Buy Goods Till 543210")
    assert data["threat_id"]
    assert isinstance(data["elapsed_ms"], int)


def test_public_response_masks_third_party_numbers(client: TestClient) -> None:
    raw = client.post("/api/v1/check", json={"handle": "@nairobi_sneakervault_official_ke"}).text
    assert "798999111" not in raw and "0798 999 111" not in raw
    assert "0798 *** 111" in raw


def test_subtle_clone_is_impersonation(client: TestClient) -> None:
    for handle in ("nairobisneakervau1t", "kiiimaniglow", "pwanlthreads"):
        data = check(client, handle=handle)
        assert data["verdict"] == "impersonation", (handle, data["score"])
        assert data["score"] >= 70


def test_look_alike_competitor_is_no_match(client: TestClient) -> None:
    for handle in ("nairobisneakerhub", "kilimanibeautybar", "pwanifashionhouse"):
        data = check(client, handle=handle)
        assert data["verdict"] == "no_match", (handle, data)
        assert data["score"] < 40
        assert data["matched_merchant"] is None
        assert data["threat_id"] is None
        assert data["safe_action"] is None


def test_official_handle_short_circuits(client: TestClient) -> None:
    data = check(client, url="instagram.com/NairobiSneakerVault/")
    assert data["verdict"] == "official"
    assert data["score"] == 0
    assert data["dimensions"] == []
    assert data["matched_merchant"]["slug"] == "nairobi-sneaker-vault"
    assert data["safe_action"]["text_sw"].startswith("Lipa tu kwa Till 543210")


def test_official_on_facebook_too(client: TestClient) -> None:
    assert check(client, url="https://m.facebook.com/kilimaniglow")["verdict"] == "official"


def test_shared_result_can_be_reopened(client: TestClient) -> None:
    first = check(client, handle="nairobi_sneakervault_official_ke")
    again = client.get(f"/api/v1/check/{first['scan_id']}")
    assert again.status_code == 200
    assert again.json()["score"] == first["score"]


def test_unknown_scan_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/check/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_invalid_input_is_422(client: TestClient) -> None:
    both = client.post("/api/v1/check", json={"url": "https://instagram.com/a", "handle": "b"})
    assert both.status_code == 422 and both.json()["error"]["code"] == "INVALID_INPUT"
    neither = client.post("/api/v1/check", json={})
    assert neither.status_code == 422
    unsupported = client.post("/api/v1/check", json={"url": "https://example.com/shop"})
    assert unsupported.status_code == 422 and unsupported.json()["error"]["code"] == "UNSUPPORTED_PLATFORM"
    post = client.post("/api/v1/check", json={"url": "https://instagram.com/p/Cxyz123/"})
    assert post.status_code == 422
    too_long = client.post("/api/v1/check", json={"url": "https://instagram.com/" + "a" * 3000})
    assert too_long.status_code == 422


def test_phone_input_points_to_verify_payment(client: TestClient) -> None:
    response = client.post("/api/v1/check", json={"handle": "0798 999 111"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PAYMENT_INPUT"


def test_unknown_page_in_demo_mode_is_502_then_manual_fallback_works(client: TestClient) -> None:
    unreachable = client.post("/api/v1/check", json={"handle": "nairobisneakervault.deals"})
    assert unreachable.status_code == 502
    assert unreachable.json()["error"]["code"] == "TARGET_UNREACHABLE"

    avatar = base64.b64encode(L.png_bytes(L.jpeg(L.sneaker_logo()))).decode()
    manual = check(
        client,
        handle="nairobisneakervault.deals",
        manual={
            "display_name": "Nairobi Sneaker Vault",
            "bio": "Lipa kwanza! Send money to 0798 555 444",
            "avatar_base64": f"data:image/png;base64,{avatar}",
        },
    )
    assert manual["target"]["fetched_via"] == "manual"
    assert manual["verdict"] == "impersonation"
    assert manual["score"] >= 90
    by_key = {d["key"]: d for d in manual["dimensions"]}
    assert by_key["visual"]["score"] == 100
    assert by_key["account"]["available"] is False


def test_manual_handle_only_is_capped_by_confidence(client: TestClient) -> None:
    data = check(client, handle="nairobisneakervau1t_ke", manual={})
    assert data["confidence"] == 0.25
    assert data["verdict"] in ("suspicious", "no_match")


def test_bad_manual_avatar_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/check", json={"handle": "somebody_new", "manual": {"avatar_base64": "bm90IGFuIGltYWdl"}}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_IMAGE"


def test_scam_page_resembling_nobody_is_no_match_with_language_reason(client: TestClient) -> None:
    data = check(client, handle="quick_loans_254", manual={"bio": "Lipa kwanza, pay before delivery"})
    assert data["verdict"] == "no_match"
    assert data["matched_merchant"] is None
    assert [r["code"] for r in data["reasons"]] == ["SCAM_LANGUAGE"]


def test_check_persists_scan_and_threat(client: TestClient, auth: dict[str, str]) -> None:
    data = check(client, handle="nairobisneakervau1t")
    threat = client.get(f"/api/v1/threats/{data['threat_id']}", headers=auth).json()
    assert threat["target"]["handle"] == "nairobisneakervau1t"
    assert threat["extracted_phones"] == ["+254711222333"]  # unmasked for the merchant
