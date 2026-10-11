"""Africa's Talking USSD channel (TSK-036, docs/future_spec.md section 1.1).

Feature-phone accessible USSD menu allowing standard consumers to input a till or phone number
and receive a Halisi verification status in plain text.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse

from app.api.deps import get_repo
from app.core.errors import InvalidInput
from app.core.repository import Repository
from app.schemas.report import ReportCreate
from app.services.payments import verify_payment

log = logging.getLogger("halisi.channels.ussd")

router = APIRouter(prefix="/channels", tags=["channels"])

WELCOME_MENU = (
    "CON Karibu Halisi!\n"
    "1. Verify Till/Paybill/Phone\n"
    "2. Report Scam Number\n"
    "3. About Halisi"
)
VERIFY_PROMPT = "CON Enter Till, Paybill or Phone number to check:"
REPORT_PROMPT = "CON Enter suspicious Till or Phone number to report:"
ABOUT_TEXT = "END Halisi protects Kenyan consumers from fake online shops & payment scams. Visit halisi.co.ke"
INVALID_CHOICE = "END Invalid choice. Please try again."
INVALID_NUMBER = (
    "END Halisi: Invalid number.\n"
    "Enter a Kenyan phone (07../01../+254..) or 5-7 digit till/paybill."
)


async def handle_ussd(
    text: str,
    phone_number: str,
    repo: Repository,
    *,
    session_id: str = "",
    service_code: str = "",
) -> str:
    """Process Africa's Talking USSD state machine.

    Protocol returns responses prefixed with:
      - ``CON `` for interactive/continued menus.
      - ``END `` for terminal messages that conclude the USSD session.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return WELCOME_MENU

    parts = [p.strip() for p in clean_text.split("*")]
    choice = parts[0]

    if choice == "1":
        if len(parts) == 1 or not parts[1]:
            return VERIFY_PROMPT

        input_value = parts[1]
        try:
            result = await verify_payment(repo, input_value)
        except (InvalidInput, ValueError):
            return INVALID_NUMBER
        except Exception:
            log.warning("Payment verification failed for USSD input: %s", input_value, exc_info=True)
            return INVALID_NUMBER

        if result.status == "official":
            name = result.merchant.business_name if result.merchant else "Verified Merchant"
            return f"END Halisi: VERIFIED OFFICIAL.\nMerchant: {name}\nStatus: Safe to pay."
        if result.status == "reported":
            return (
                "END Halisi: ONYO! REPORTED SCAM.\n"
                "Number linked to scam reports. DO NOT SEND MONEY."
            )
        # unknown
        return (
            "END Halisi: UNKNOWN NUMBER.\n"
            "Not registered with verified merchants. Verify carefully before paying."
        )

    if choice == "2":
        if len(parts) == 1 or not parts[1]:
            return REPORT_PROMPT

        number = parts[1]
        try:
            is_phone = number.startswith(("+", "07", "01", "254")) or len(number) >= 9
            await repo.insert_report(
                ReportCreate(
                    reported_phone=number if is_phone else None,
                    reported_till=None if is_phone else number,
                    description="Reported via USSD",
                    reporter_contact=phone_number or None,
                )
            )
        except Exception:
            log.warning("Could not persist USSD community report for number: %s", number, exc_info=True)

        return f"END Asante! Scam report received for {number}. Halisi team is investigating."

    if choice == "3":
        return ABOUT_TEXT

    return INVALID_CHOICE


@router.post("/ussd", response_class=PlainTextResponse)
async def ussd_endpoint(
    repo: Annotated[Repository, Depends(get_repo)],
    sessionId: Annotated[str | None, Form()] = None,
    serviceCode: Annotated[str | None, Form()] = None,
    phoneNumber: Annotated[str | None, Form()] = None,
    text: Annotated[str | None, Form()] = "",
    session_id: Annotated[str | None, Form()] = None,
    service_code: Annotated[str | None, Form()] = None,
    phone_number: Annotated[str | None, Form()] = None,
) -> PlainTextResponse:
    """Africa's Talking USSD callback endpoint."""
    effective_session_id = sessionId or session_id or ""
    effective_service_code = serviceCode or service_code or ""
    effective_phone_number = phoneNumber or phone_number or ""
    effective_text = text or ""

    reply = await handle_ussd(
        text=effective_text,
        phone_number=effective_phone_number,
        repo=repo,
        session_id=effective_session_id,
        service_code=effective_service_code,
    )
    return PlainTextResponse(content=reply, media_type="text/plain")