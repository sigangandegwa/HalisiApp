"""Telegram consumer checker bot (TSK-042, docs/BACKEND.md section 5, future_spec.md section 1.2).

Allows consumers to forward Instagram/TikTok profiles, handles, or M-Pesa payment numbers
to receive an instant Forensic Verdict (HALISI / FEKI / TAHADHARI).
"""

import logging
import re
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.deps import get_check_service, get_repo, get_settings
from app.core.config import Settings
from app.core.errors import PaymentInput, TargetUnreachable, UnsupportedPlatform
from app.core.logging import log_event
from app.core.repository import Repository
from app.ingestion.url_parser import ParsedInput, UnsupportedInput, parse_input
from app.schemas.check import CheckRequest, CheckResult
from app.schemas.report import VerifyPaymentResult
from app.services.check import CheckService, perform_check
from app.services.payments import verify_payment

log = logging.getLogger("halisi.channels.telegram")
router = APIRouter()

URL_REGEX = re.compile(r"https?://[^\s]+", re.IGNORECASE)
HANDLE_REGEX = re.compile(r"@[a-zA-Z0-9._]{1,60}")
PHONE_TILL_REGEX = re.compile(r"\b(?:\+?254\d{9}|0[17]\d{8}|\d{5,7})\b")


def extract_target(text: str) -> ParsedInput | None:
    """Extract a valid ParsedInput from free-form message text.

    Supports:
    - Direct URLs, handles, phone and till numbers
    - Prefixed commands like /check <target> or /verify <target>
    - Messages with embedded URLs, @handles, or payment numbers
    """
    raw = (text or "").strip()
    if not raw:
        return None

    # Strip command prefix if provided (e.g. "/check https://instagram.com/foo")
    for cmd in ("/check", "/verify", "/halisi"):
        if raw.lower().startswith(cmd):
            raw = raw[len(cmd) :].strip()
            break

    if not raw:
        return None

    # 1. Try parsing directly
    try:
        return parse_input(raw)
    except UnsupportedInput:
        pass

    # 2. Extract embedded URLs
    urls = URL_REGEX.findall(raw)
    for candidate in urls:
        cleaned = candidate.rstrip(".,!?:;)\"'")
        try:
            return parse_input(cleaned)
        except UnsupportedInput:
            continue

    # 3. Extract @handles
    handles = HANDLE_REGEX.findall(raw)
    for candidate in handles:
        try:
            return parse_input(candidate)
        except UnsupportedInput:
            continue

    # 4. Extract phones or tills
    numbers = PHONE_TILL_REGEX.findall(raw)
    for candidate in numbers:
        try:
            return parse_input(candidate)
        except UnsupportedInput:
            continue

    return None


def format_welcome_message() -> str:
    """Friendly welcome message for /start."""
    return (
        "🇰🇪 *Karibu Halisi Bot!*\n\n"
        "Halisi protects you from online scams and brand impersonation on "
        "Instagram, TikTok, Facebook, and X.\n\n"
        "*How to use:*\n"
        "• Forward or paste any profile link or `@handle` (e.g. `https://instagram.com/brand`).\n"
        "• Send an M-Pesa Till or Phone number to check against verified merchant records.\n\n"
        "Send `/help` for guidance, or paste a link now to check!"
    )


def format_help_message() -> str:
    """Help guide explaining forensic verdicts."""
    return (
        "🛡️ *Halisi Bot Guide*\n\n"
        "Send any profile link, handle, or payment number to receive an instant Forensic Verdict:\n\n"
        "• 🟢 *HALISI (Official)*: Verified authentic merchant account. Safe to transact.\n"
        "• ⚠️ *TAHADHARI (Caution)*: Suspicious signals detected. Proceed with caution.\n"
        "• 🔴 *FEKI (Impersonation)*: Confirmed clone or scam. DO NOT send money!\n"
        "• ⚪ *NO MATCH*: No registered Halisi merchant matches this handle.\n\n"
        "*Supported formats:*\n"
        "• Profile URLs: Instagram, TikTok, Facebook, X\n"
        "• Social handles: `@merchant_name`\n"
        "• M-Pesa details: Buy Goods Till, Paybill, or Phone number\n\n"
        "Stay vigilant and protect your money! 🇰🇪"
    )


def format_unsupported_message() -> str:
    """Fallback response for unrecognized inputs."""
    return (
        "🤔 *Halisi couldn't find a valid link or number in your message.*\n\n"
        "Please send or forward:\n"
        "• A social profile URL (Instagram, TikTok, Facebook, X)\n"
        "• A handle like `@brandname`\n"
        "• An M-Pesa phone or till number\n\n"
        "Type `/help` for examples."
    )


def format_check_result(result: CheckResult) -> str:
    """Format Forensic Verdict for Telegram."""
    verdict = result.verdict
    target_handle = result.target.handle or "unknown"
    platform = (result.target.platform or "").title()
    score_int = int(round(result.score))

    merchant_name = result.matched_merchant.business_name if result.matched_merchant else None

    if verdict == "official":
        verdict_badge = "🟢 *HALISI (Official Account)*"
        advice = (
            result.safe_action.text
            if result.safe_action and result.safe_action.text
            else f"Verified official page for {merchant_name or 'the merchant'}. Safe to transact!"
        )
        return (
            f"🔍 *Halisi Forensic Verdict*\n\n"
            f"⚖️ Verdict: {verdict_badge}\n"
            f"📊 Risk Score: *{score_int} / 100*\n"
            f"🎯 Target: `@{target_handle}` ({platform})\n"
            f"🏢 Verified Merchant: *{merchant_name or 'Verified Business'}*\n\n"
            f"🛡️ *Official Advice:*\n{advice}"
        )

    if verdict == "impersonation":
        verdict_badge = "🔴 *FEKI (Impersonation / Clone)*"
    elif verdict == "suspicious":
        verdict_badge = "⚠️ *TAHADHARI (Suspicious Account)*"
    else:
        verdict_badge = "⚪ *NO MATCH (Hakuna Ulinganisho)*"

    lines = [
        "🔍 *Halisi Forensic Verdict*",
        "",
        f"⚖️ Verdict: {verdict_badge}",
        f"📊 Risk Score: *{score_int} / 100*",
        f"🎯 Target: `@{target_handle}` ({platform})",
    ]

    if merchant_name:
        relation = "🏢 Imitating:" if verdict == "impersonation" else "🏢 Potential Match:"
        lines.append(f"{relation} *{merchant_name}*")

    if result.reasons:
        lines.append("\n⚠️ *Risk Indicators:*")
        for r in result.reasons:
            lines.append(f"• {r.text}")

    if result.safe_action and result.safe_action.text:
        lines.append(f"\n🛡️ *Official Advice:*\n{result.safe_action.text}")
    elif verdict == "no_match":
        lines.append(
            "\n🛡️ *Official Advice:*\n"
            "No registered Halisi merchant matches this handle. "
            "Always verify payment details through official brand channels before transacting."
        )

    return "\n".join(lines)


def format_payment_result(result: VerifyPaymentResult) -> str:
    """Format payment verification verdict for Telegram."""
    status = result.status
    kind_upper = result.kind.upper()
    display_num = result.display

    if status == "official":
        merchant_name = result.merchant.business_name if result.merchant else "Verified Merchant"
        return (
            f"🔍 *Halisi Payment Verification*\n\n"
            f"⚖️ Status: 🟢 *HALISI (Official Payment Channel)*\n"
            f"📱 Number: `{display_num}` ({kind_upper})\n"
            f"🏢 Registered to: *{merchant_name}*\n\n"
            f"🛡️ Safe to transact with this merchant."
        )

    if status == "reported":
        return (
            f"🔍 *Halisi Payment Verification*\n\n"
            f"⚖️ Status: 🔴 *FEKI / HATARI (Reported Scam Risk)*\n"
            f"📱 Number: `{display_num}` ({kind_upper})\n"
            f"⚠️ Scam Reports: *{result.report_count} confirmed report(s)*\n"
            f"🔗 Linked Threats: *{result.linked_threats} active threat(s)*\n\n"
            f"🚨 *Warning:* This payment number has been flagged for scam activity. DO NOT SEND MONEY!"
        )

    return (
        f"🔍 *Halisi Payment Verification*\n\n"
        f"⚖️ Status: ⚠️ *TAHADHARI (Unknown / Unregistered)*\n"
        f"📱 Number: `{display_num}` ({kind_upper})\n\n"
        f"ℹ️ This number is not registered with Halisi. We cannot verify if it belongs "
        f"to a legitimate business. Exercise caution and double-check with the seller directly!"
    )


async def process_telegram_message(
    text: str,
    service: CheckService,
    repo: Repository,
    *,
    background: BackgroundTasks | None = None,
) -> str:
    """Process a consumer message and return the response text."""
    raw = (text or "").strip()

    if raw.startswith("/start"):
        return format_welcome_message()

    if raw.startswith("/help"):
        return format_help_message()

    parsed = extract_target(raw)
    if parsed is None:
        return format_unsupported_message()

    if parsed.is_payment:
        result = await verify_payment(repo, parsed.value or parsed.number or "")
        return format_payment_result(result)

    try:
        if parsed.kind == "url":
            req = CheckRequest(url=parsed.url or parsed.value)
        else:
            req = CheckRequest(
                handle=parsed.handle or parsed.value,
                platform=parsed.platform,  # type: ignore[arg-type]
            )
        outcome = await perform_check(service, req, source="public_checker")
        if background is not None:
            background.add_task(service.persist, outcome)
        return format_check_result(outcome.result)
    except TargetUnreachable:
        platform_name = parsed.platform.title() if parsed.platform else "the platform"
        return (
            f"⚠️ *Account Unreachable*\n\n"
            f"Could not reach or inspect `@{parsed.handle}` on {platform_name}. "
            f"The account might be private, suspended, or unreachable.\n\n"
            f"Tip: If they shared an M-Pesa till/phone, send it here to verify payment details."
        )
    except UnsupportedPlatform:
        return (
            "❌ *Unsupported Platform*\n\n"
            "Halisi supports Instagram, TikTok, Facebook, and X profile links."
        )
    except PaymentInput:
        result = await verify_payment(repo, parsed.value or parsed.number or "")
        return format_payment_result(result)
    except Exception as exc:  # noqa: BLE001
        log_event("telegram_check_error", error=str(exc))
        return (
            "⚠️ *Check Failed*\n\n"
            "An unexpected error occurred while analyzing this target. Please try again later."
        )


async def send_telegram_message(
    token: str,
    chat_id: int | str,
    text: str,
    *,
    http_client: httpx.AsyncClient | None = None,
    parse_mode: str = "Markdown",
) -> dict[str, Any] | None:
    """Send an outbound Telegram message via the Bot API.

    Returns None if token is empty or request fails.
    """
    if not token:
        log.warning("send_telegram_message skipped: TELEGRAM_BOT_TOKEN not configured")
        return None

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}

    client = http_client or httpx.AsyncClient(timeout=10.0)
    should_close = http_client is None
    try:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        log.warning("Telegram API error: %s - %s", response.status_code, response.text)
        return None
    except httpx.HTTPError as exc:
        log.warning("Telegram request failed: %r", exc)
        return None
    finally:
        if should_close:
            await client.aclose()


@router.post("/webhook")
async def telegram_webhook(
    update: dict[str, Any],
    background: BackgroundTasks,
    service: Annotated[CheckService, Depends(get_check_service)],
    repo: Annotated[Repository, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """Handle incoming Telegram webhook updates."""
    if not settings.telegram_bot_token:
        log.warning("telegram webhook called but TELEGRAM_BOT_TOKEN is not configured")
        return {
            "ok": False,
            "status": "disabled",
            "description": "TELEGRAM_BOT_TOKEN is not configured",
        }

    message = (
        update.get("message")
        or update.get("edited_message")
        or update.get("channel_post")
    )
    if not message or not isinstance(message, dict):
        return {"ok": True, "status": "ignored", "description": "No actionable message found"}

    chat = message.get("chat")
    chat_id = chat.get("id") if isinstance(chat, dict) else None
    if chat_id is None:
        return {"ok": True, "status": "ignored", "description": "No chat id found"}

    text = message.get("text") or message.get("caption") or ""
    response_text = await process_telegram_message(text, service, repo, background=background)

    return {
        "ok": True,
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": response_text,
        "parse_mode": "Markdown",
    }
