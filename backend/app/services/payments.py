"""``GET /verify/payment`` (TSK-022, docs/BACKEND.md section 5.3): is this phone/till official or reported?"""

from app.core.errors import InvalidInput
from app.core.repository import Repository
from app.ingestion.url_parser import UnsupportedInput, parse_input
from app.schemas.report import VerifyPaymentResult
from app.services.serializers import display_number, public_merchant


async def verify_payment(repo: Repository, value: str) -> VerifyPaymentResult:
    """Look a phone / till / wa.me link up.

    * ``official``: registered to a Halisi merchant (the merchant's public profile is returned)
    * ``reported``: at least one **confirmed** community report, or listed on an active impersonation
      threat. Pending reports alone don't flip the status (one person can't brand a number a scam),
      but they are counted in ``report_count``.
    * ``unknown``: "not registered with Halisi". Never phrase it as "safe".

    Raises InvalidInput for anything that isn't a Kenyan mobile number or a 5-7 digit till/paybill.
    """
    try:
        parsed = parse_input(value)
    except UnsupportedInput as exc:
        raise InvalidInput(
            "Enter a Kenyan phone number (07.. / 01.. / +254..) or a 5-7 digit till/paybill."
        ) from exc
    if not parsed.is_payment or parsed.number is None:
        raise InvalidInput("Enter a Kenyan phone number (07.. / 01.. / +254..) or a 5-7 digit till/paybill.")
    number = parsed.number
    kind = "phone" if number.startswith("+") else "till"
    facts = await repo.find_by_payment(
        number if kind == "phone" else None, number if kind == "till" else None
    )
    if facts.merchant is not None:
        status = "official"
    elif facts.confirmed_reports > 0 or facts.linked_threats > 0:
        status = "reported"
    else:
        status = "unknown"
    return VerifyPaymentResult(
        kind=kind,
        normalized=number,
        display=display_number(number, official=status == "official"),
        status=status,
        merchant=public_merchant(facts.merchant) if facts.merchant else None,
        report_count=facts.report_count,
        linked_threats=facts.linked_threats,
    )
