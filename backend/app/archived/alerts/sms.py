"""Africa's Talking SMS integration for critical impersonation alerts (TSK-041).

Connects to Africa's Talking SMS API:
- Live endpoint: https://api.africastalking.com/version1/messaging
- Sandbox endpoint: https://api.sandbox.africastalking.com/version1/messaging

When AFRICASTALKING_API_KEY / AFRICASTALKING_USERNAME are not configured or DEMO_MODE=True,
it logs the simulated SMS and gracefully succeeds without making network requests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import log_event
from app.engine.payment import canonical_phone, mask_phone

AT_LIVE_URL = "https://api.africastalking.com/version1/messaging"
AT_SANDBOX_URL = "https://api.sandbox.africastalking.com/version1/messaging"
DEFAULT_TIMEOUT = 10.0


@dataclass(slots=True)
class SMSResult:
    """Outcome of an SMS dispatch operation."""

    success: bool
    simulated: bool
    message: str
    recipient: str
    response: dict[str, Any] | None = None
    error: str | None = None

    def __bool__(self) -> bool:
        return self.success


def format_threat_sms(merchant_name: str, threat_handle: str, score: float) -> str:
    """Format a concise, urgent SMS in English/Swahili alert style."""
    handle = threat_handle.strip()
    if not handle.startswith("@"):
        handle = f"@{handle}"
    return (
        f"HALISI TAHADHARI / ALERT: Impersonator {handle} detected mimicking {merchant_name} "
        f"(Risk: {score:.0f}%). Akaunti feki imegunduliwa. Fungua dashibodi yako kuchukua hatua."
    )


def normalize_phone(phone_number: str) -> str:
    """Normalize phone number to E.164 format (+254...), falling back cleanly."""
    canon = canonical_phone(phone_number)
    if canon:
        return canon
    cleaned = phone_number.strip()
    if cleaned.startswith("+"):
        return cleaned
    digits = re.sub(r"\D", "", cleaned)
    if digits.startswith("254"):
        return f"+{digits}"
    return f"+{digits}" if digits else phone_number


def get_messaging_url(username: str) -> str:
    """Return sandbox or production URL depending on username."""
    if username.strip().lower() == "sandbox":
        return AT_SANDBOX_URL
    return AT_LIVE_URL


async def send_threat_sms(
    phone_number: str,
    merchant_name: str,
    threat_handle: str,
    score: float,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> SMSResult:
    """Send an urgent SMS alert for a critical impersonation threat.

    When unconfigured or running in DEMO_MODE, logs simulated dispatch and returns success.
    """
    cfg = settings or get_settings()
    recipient = normalize_phone(phone_number)
    message = format_threat_sms(merchant_name, threat_handle, score)

    # Fallback to simulation if unconfigured or in demo mode
    if cfg.demo_mode or not cfg.africastalking_api_key or not cfg.africastalking_username:
        reason = "demo_mode" if cfg.demo_mode else "unconfigured"
        log_event(
            "sms_simulated",
            recipient=mask_phone(recipient),
            merchant=merchant_name,
            threat=threat_handle,
            score=score,
            body=message,
            reason=reason,
        )
        return SMSResult(
            success=True,
            simulated=True,
            message=message,
            recipient=recipient,
            response={"status": "simulated", "reason": reason},
        )

    url = get_messaging_url(cfg.africastalking_username)
    data: dict[str, str] = {
        "username": cfg.africastalking_username,
        "to": recipient,
        "message": message,
    }
    if cfg.africastalking_sender_id:
        data["from"] = cfg.africastalking_sender_id

    headers = {
        "apiKey": cfg.africastalking_api_key,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        if client is not None:
            resp = await client.post(url, data=data, headers=headers, timeout=DEFAULT_TIMEOUT)
        else:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as http:
                resp = await http.post(url, data=data, headers=headers)

        if resp.status_code in (200, 201):
            try:
                payload: dict[str, Any] = resp.json()
            except Exception:
                payload = {"text": resp.text}

            # Check AT recipients response for status
            recipients = payload.get("SMSMessageData", {}).get("Recipients", [])
            failed = [
                r
                for r in recipients
                if r.get("status") not in ("Success", "Sent", "Queued")
                and r.get("statusCode") not in (100, 101, 102)
            ]
            if failed and not any(
                r.get("status") in ("Success", "Sent", "Queued") or r.get("statusCode") in (100, 101, 102)
                for r in recipients
            ):
                err_msg = f"Africa's Talking recipient failed: {failed}"
                log_event("sms_failed", recipient=mask_phone(recipient), error=err_msg)
                return SMSResult(
                    success=False,
                    simulated=False,
                    message=message,
                    recipient=recipient,
                    response=payload,
                    error=err_msg,
                )

            log_event("sms_sent", recipient=mask_phone(recipient), merchant=merchant_name, status="sent")
            return SMSResult(
                success=True,
                simulated=False,
                message=message,
                recipient=recipient,
                response=payload,
            )

        err_msg = f"Africa's Talking returned HTTP {resp.status_code}: {resp.text}"
        log_event("sms_failed", recipient=mask_phone(recipient), error=err_msg)
        return SMSResult(
            success=False,
            simulated=False,
            message=message,
            recipient=recipient,
            error=err_msg,
        )
    except Exception as exc:
        err_msg = f"Africa's Talking request error: {exc}"
        log_event("sms_error", recipient=mask_phone(recipient), error=err_msg)
        return SMSResult(
            success=False,
            simulated=False,
            message=message,
            recipient=recipient,
            error=err_msg,
        )


class AfricasTalkingClient:
    """Class wrapper for Africa's Talking SMS API operations."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client

    async def send_threat_sms(
        self,
        phone_number: str,
        merchant_name: str,
        threat_handle: str,
        score: float,
    ) -> SMSResult:
        """Send an urgent threat SMS alert."""
        return await send_threat_sms(
            phone_number,
            merchant_name,
            threat_handle,
            score,
            settings=self.settings,
            client=self.client,
        )
