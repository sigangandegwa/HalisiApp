"""Merchant ownership proof by bio code (TSK-044, docs/PRODUCT_V2.md section 5).

A merchant onboards as ``claimed`` with a one-time code (``halisi-ab12cd``). They put the code in the
bio of an official handle they declared; :func:`check_verification` fetches the public bio and, if the
code is there, promotes them to ``verified``. Only a person who controls the account can edit its bio,
which is the proof a self-declared brand claim lacks.
"""

import secrets

from app.core.errors import VerificationFailed
from app.core.repository import Repository, utcnow
from app.schemas.merchant import MerchantRecord, VerificationState
from app.services.check import CheckService

CODE_PREFIX = "halisi-"
FETCHABLE_PLATFORMS = ("instagram", "tiktok", "facebook", "x")


def new_code() -> str:
    """A short one-time code that fits in a bio: ``halisi-`` + 6 hex characters."""
    return CODE_PREFIX + secrets.token_hex(3)


def verification_state(merchant: MerchantRecord, *, checked: list[str] | None = None) -> VerificationState:
    """The merchant's verification state. The code is only shown while the merchant is still ``claimed``."""
    claimed = merchant.verification_status == "claimed"
    handles = [h for h in merchant.official_handles if h.platform in FETCHABLE_PLATFORMS]
    return VerificationState(
        status=merchant.verification_status,
        is_verified=merchant.is_verified,
        verification_code=merchant.verification_code if claimed else None,
        handles_to_check=handles if claimed else [],
        checked=checked or [],
        verified_at=merchant.verified_at,
        instructions=(
            f"Add {merchant.verification_code} to the bio of one of your official accounts, "
            "then press Verify. You can remove it afterwards."
            if claimed and merchant.verification_code
            else None
        ),
    )


async def check_verification(
    repo: Repository, service: CheckService, merchant: MerchantRecord
) -> VerificationState:
    """Look for the merchant's code in the bios of its official handles and promote it if found.

    Idempotent for merchants that are already verified or curated. Raises VerificationFailed when
    the code is not found (or no handle could be read), so the UI can say "not there yet".
    """
    if merchant.verification_status != "claimed":
        return verification_state(merchant)
    code = (merchant.verification_code or "").lower()
    checked: list[str] = []
    for handle in merchant.official_handles:
        if handle.platform not in FETCHABLE_PLATFORMS:
            continue
        checked.append(f"{handle.platform}:{handle.handle}")
        bio = await service.fetch_bio(handle.platform, handle.handle, handle.url)
        if code and bio and code in bio.lower():
            updated = await repo.mark_verified(merchant.id, utcnow())
            service.merchants.invalidate()
            state = verification_state(updated, checked=checked)
            return state.model_copy(update={"found_on": checked[-1]})
    where = ", ".join(checked) if checked else "any handle (add an Instagram, TikTok, Facebook or X handle)"
    raise VerificationFailed(f"We could not find {merchant.verification_code} in the bio of {where} yet.")
