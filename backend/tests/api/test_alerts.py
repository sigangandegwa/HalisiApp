"""In-app alerts (TSK-012, docs/BACKEND.md section 8): dispatcher rules + alert endpoints, DEMO_MODE."""

import base64
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.alerts.dispatcher import decide_kind, dispatch_threat_alert
from app.core.repository import MemoryRepository
from app.ingestion.fixtures import logos as L
from app.ingestion.mock_seeder import seed_id
from app.schemas.threat import ThreatUpsert

NSV = str(seed_id("merchant", "nsv"))
LOGO_B64 = base64.b64encode(L.png_bytes(L.sneaker_logo())).decode()


def alerts(client: TestClient, auth: dict[str, str], **params: object) -> dict:
    response = client.get(f"/api/v1/merchants/{NSV}/alerts", headers=auth, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_seed_created_one_alert_per_seeded_threat(client: TestClient, auth: dict[str, str]) -> None:
    data = alerts(client, auth)
    assert data["unread_count"] == 2
    assert {a["kind"] for a in data["alerts"]} == {"new_threat"}
    titles = {a["title"] for a in data["alerts"]}
    assert "Impersonator detected: @nairobi_sneakervault_official_ke" in titles
    first = data["alerts"][0]
    assert first["threat"]["target_handle"] and first["threat"]["composite_score"] >= 70
    assert "798" not in first["title"] + first["body"]  # no phone numbers in notifications
    assert datetime.fromisoformat(data["server_time"])


def test_new_clone_creates_exactly_one_alert_and_a_repeat_creates_none(
    client: TestClient, auth: dict[str, str]
) -> None:
    cursor = alerts(client, auth)["server_time"]
    body = {
        "handle": "nairobisneakervault.kenya",
        "manual": {"bio": "Send money to 0798 555 444", "avatar_base64": LOGO_B64},
    }
    assert client.post("/api/v1/check", json=body).json()["verdict"] == "impersonation"
    new = alerts(client, auth, since=cursor)
    assert [a["kind"] for a in new["alerts"]] == ["new_threat"]
    assert new["alerts"][0]["title"] == "Impersonator detected: @nairobisneakervault.kenya"
    assert new["unread_count"] == 3

    cursor = new["server_time"]
    client.post("/api/v1/check", json=body)  # same page again, same score
    assert alerts(client, auth, since=cursor)["alerts"] == []


def test_score_rise_of_ten_creates_score_increase(client: TestClient, auth: dict[str, str]) -> None:
    handle = "nairobisneakervault_hq"
    low = client.post("/api/v1/check", json={"handle": handle, "manual": {"bio": "New stock"}}).json()
    assert 70 <= low["score"] < 80 and low["threat_id"]  # identity only: stored as a threat
    cursor = alerts(client, auth)["server_time"]
    high = client.post(
        "/api/v1/check",
        json={
            "handle": handle,
            "manual": {"bio": "Lipa kwanza. Send money to 0798 555 444", "avatar_base64": LOGO_B64},
        },
    ).json()
    assert high["score"] - low["score"] >= 10
    new = alerts(client, auth, since=cursor)["alerts"]
    assert [a["kind"] for a in new] == ["score_increase"]
    assert new[0]["title"].startswith("Score rose to ")


def test_unread_filter_and_mark_read(client: TestClient, auth: dict[str, str]) -> None:
    data = alerts(client, auth, unread="true")
    assert len(data["alerts"]) == 2
    one = data["alerts"][0]["id"]
    marked = client.post(f"/api/v1/merchants/{NSV}/alerts/read", json={"ids": [one]}, headers=auth)
    assert marked.json() == {"unread_count": 1}
    assert len(alerts(client, auth, unread="true")["alerts"]) == 1
    assert client.post(f"/api/v1/merchants/{NSV}/alerts/read", json={"all": True}, headers=auth).json() == {
        "unread_count": 0
    }
    assert alerts(client, auth)["alerts"][0]["read_at"] is not None
    assert client.post(f"/api/v1/merchants/{NSV}/alerts/read", json={}, headers=auth).status_code == 422


def test_since_cursor_returns_only_newer_rows(client: TestClient, auth: dict[str, str]) -> None:
    future = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    assert alerts(client, auth, since=future)["alerts"] == []
    assert len(alerts(client, auth, since="2000-01-01T00:00:00Z")["alerts"]) == 2


def test_resolving_a_threat_writes_a_resolved_alert(client: TestClient, auth: dict[str, str]) -> None:
    threat_id = client.get(f"/api/v1/merchants/{NSV}/threats", headers=auth).json()[0]["id"]
    cursor = alerts(client, auth)["server_time"]
    patched = client.patch(f"/api/v1/threats/{threat_id}", json={"status": "resolved"}, headers=auth)
    assert patched.status_code == 200
    body = patched.json()
    assert body["status"] == "resolved" and body["resolved_at"]
    assert [e["status"] for e in body["status_history"]] == ["detected", "resolved"]
    assert [a["kind"] for a in alerts(client, auth, since=cursor)["alerts"]] == ["resolved"]


def test_alerts_need_the_key_and_a_real_merchant(client: TestClient, auth: dict[str, str]) -> None:
    assert client.get(f"/api/v1/merchants/{NSV}/alerts").status_code == 401
    assert client.get(f"/api/v1/merchants/{uuid4()}/alerts", headers=auth).status_code == 404


# --- dispatcher unit rules ----------------------------------------------------------------------


def _upsert(merchant_id, score: float) -> ThreatUpsert:
    return ThreatUpsert(
        merchant_id=merchant_id,
        platform="instagram",
        target_handle="fake_shop",
        target_url="https://instagram.com/fake_shop",
        composite_score=score,
        reasons=[
            {
                "code": "PAYMENT_MISMATCH",
                "severity": "high",
                "text": "Asks you to pay 0798 999 111.",
                "text_sw": "...",
            }
        ],
    )


async def test_dispatcher_rules_and_dedup() -> None:
    repo = MemoryRepository()
    merchant_id = uuid4()
    below = await repo.upsert_threat(_upsert(merchant_id, 60))
    assert decide_kind(None, below, 70) is None

    t0 = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
    created = await repo.upsert_threat(_upsert(uuid4(), 92))
    first = await dispatch_threat_alert(repo, None, created, threshold=70, dedup_hours=6, now=t0)
    assert first is not None and first.kind == "new_threat"
    assert "0798" not in first.body and "a number" in first.body
    again = await dispatch_threat_alert(
        repo, None, created, threshold=70, dedup_hours=6, now=t0 + timedelta(hours=1)
    )
    assert again is None  # de-duplicated within 6 h
    later = await dispatch_threat_alert(
        repo, None, created, threshold=70, dedup_hours=6, now=t0 + timedelta(hours=7)
    )
    assert later is not None

    crossed = created.model_copy(update={"composite_score": 75})
    assert decide_kind(below, crossed, 70) == "score_increase"  # crossed the threshold
    assert decide_kind(created, created.model_copy(update={"composite_score": 95}), 70) is None  # +3 only
    fp = created.model_copy(update={"status": "false_positive", "composite_score": 100})
    assert decide_kind(created, fp, 70) is None
