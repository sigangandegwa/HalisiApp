"""Playbook generation (TSK-009): NVIDIA NIM (OpenAI-compatible client), validated, template fallback.

Human in the loop: Halisi drafts, the merchant sends. Nothing here emails anyone.
"""

import asyncio
import logging
from typing import Protocol

from app.core.config import Settings
from app.core.repository import Repository
from app.engine import remediation as rem
from app.engine.scorer import safe_action
from app.schemas.merchant import MerchantRecord
from app.schemas.remediation import (
    ConsumerWarning,
    KecirtReport,
    PlatformTakedown,
    PlaybooksResponse,
    RemediationCreate,
    SafaricomReport,
)
from app.schemas.threat import ThreatRecord
from app.services.serializers import merchant_profile

log = logging.getLogger("halisi.remediation")
KINDS: tuple[rem.PlaybookKind, ...] = (
    "consumer_warning",
    "platform_takedown",
    "safaricom_report",
    "kecirt_report",
)
REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    "consumer_warning": ("title", "body"),
    "platform_takedown": ("body",),
    "safaricom_report": ("subject", "body"),
    "kecirt_report": ("subject", "body"),
}


class LlmClient(Protocol):
    """Anything that turns chat messages into raw text (the NIM client, or a fake in tests)."""

    model: str

    async def complete(self, messages: list[dict[str, str]]) -> str: ...


class NimClient:
    """NVIDIA NIM (hosted build.nvidia.com or self-hosted) through ``openai.AsyncOpenAI``."""

    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI

        self.model = settings.llm_model
        self.timeout = settings.llm_timeout_seconds
        self._client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=settings.llm_timeout_seconds,
            max_retries=0,
        )

    async def complete(self, messages: list[dict[str, str]]) -> str:
        """One chat completion, temperature 0.3."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=700,  # type: ignore[arg-type]
        )
        return response.choices[0].message.content or ""


def build_facts(threat: ThreatRecord, merchant: MerchantRecord) -> rem.RemediationFacts:
    """Facts object from DB records: the only thing the LLM (or a template) may state."""
    profile = merchant_profile(merchant)
    en, sw = safe_action(profile, threat.platform)
    distance = None
    if threat.avatar_phash and merchant.logo_phash:
        from app.engine.hasher import hamming

        try:
            distance = hamming(threat.avatar_phash.strip(), merchant.logo_phash.strip())
        except ValueError:
            distance = None
    reasons_en = [str(r.get("text", "")) for r in threat.reasons if r.get("text")]
    reasons_sw = [str(r.get("text_sw", "")) for r in threat.reasons if r.get("text_sw")]
    return rem.RemediationFacts(
        merchant_name=merchant.business_name,
        official_handles=[f"@{h.handle} ({h.platform})" for h in merchant.official_handles],
        official_handle_names=[h.handle for h in merchant.official_handles],
        payment_type=merchant.mpesa_type,
        payment_number=merchant.mpesa_number,
        payment_account_name=merchant.mpesa_account_name,
        safe_action_en=en,
        safe_action_sw=sw,
        target_platform=threat.platform,
        target_handle=threat.target_handle,
        target_url=threat.target_url,
        target_display_name=threat.display_name,
        extracted_phones=list(threat.extracted_phones),
        extracted_tills=list(threat.extracted_tills),
        composite_score=threat.composite_score,
        confidence=threat.confidence,
        visual_score=threat.visual_score,
        identity_score=threat.identity_score,
        payment_score=threat.payment_score,
        language_score=threat.language_score,
        account_score=threat.account_score,
        phash_distance=distance,
        first_seen_on=threat.first_seen_at.date().isoformat(),
        reasons_en=reasons_en,
        reasons_sw=reasons_sw,
        bio=threat.bio,
    )


async def _llm_playbook(
    llm: LlmClient, kind: rem.PlaybookKind, facts: rem.RemediationFacts, lang: rem.Lang
) -> dict[str, str] | None:
    """One LLM playbook, validated. None (with a logged reason) means: use the template."""
    try:
        raw = await llm.complete(rem.build_messages(kind, facts, lang))
        data = rem.parse_llm_json(raw)
    except Exception as exc:  # noqa: BLE001 - timeout, HTTP error, bad JSON: all fall back
        log.warning("playbook %s: LLM failed (%s), using template", kind, type(exc).__name__)
        return None
    missing = [k for k in REQUIRED_KEYS[kind] if not data.get(k, "").strip()]
    if missing:
        log.warning("playbook %s: LLM output missing %s, using template", kind, missing)
        return None
    problems = [p for key in REQUIRED_KEYS[kind] for p in rem.validate_output(data[key], facts)]
    if problems:
        log.warning("playbook %s: LLM output rejected (%s), using template", kind, "; ".join(problems[:3]))
        return None
    if kind == "consumer_warning":
        data["body"] = data["body"][: rem.CONSUMER_WARNING_MAX]
    return {k: data[k] for k in REQUIRED_KEYS[kind]}


async def generate_playbooks(
    repo: Repository,
    threat: ThreatRecord,
    merchant: MerchantRecord,
    lang: rem.Lang,
    llm: LlmClient | None,
) -> PlaybooksResponse:
    """All four playbooks. LLM when available (in parallel), template per playbook on any failure."""
    facts = build_facts(threat, merchant)
    outputs: dict[str, tuple[dict[str, str], str]] = {}
    llm_results: list[dict[str, str] | None] = [None] * len(KINDS)
    if llm is not None:
        llm_results = list(await asyncio.gather(*(_llm_playbook(llm, k, facts, lang) for k in KINDS)))
    for kind, llm_out in zip(KINDS, llm_results, strict=True):
        outputs[kind] = (llm_out, "llm") if llm_out else (rem.render_playbook(kind, facts, lang), "template")

    for kind, (content, generator) in outputs.items():
        text = "\n\n".join(content[k] for k in REQUIRED_KEYS[kind])
        await repo.insert_remediation(
            RemediationCreate(
                threat_id=threat.id,
                playbook_type=kind,
                language=lang,
                generated_content=text,
                generator=generator,  # type: ignore[arg-type]
                prompt_id=rem.PROMPT_IDS[kind],
                model=llm.model if llm and generator == "llm" else None,
            )
        )

    all_llm = all(g == "llm" for _, g in outputs.values())
    channels = rem.channels()
    cw, cw_gen = outputs["consumer_warning"]
    pt, pt_gen = outputs["platform_takedown"]
    sr, sr_gen = outputs["safaricom_report"]
    kr, kr_gen = outputs["kecirt_report"]
    share_text = f"{cw['title']}\n{cw['body']}"
    return PlaybooksResponse(
        generator="llm" if all_llm else "template",
        model=llm.model if llm is not None and any(g == "llm" for _, g in outputs.values()) else None,
        language=lang,
        prompt_ids=[rem.PROMPT_IDS[k] for k in KINDS],
        consumer_warning=ConsumerWarning(
            title=cw["title"],
            body=cw["body"],
            whatsapp_share_url=rem.whatsapp_share_url(share_text),
            generator=cw_gen,
        ),
        platform_takedown=PlatformTakedown(
            platform=threat.platform,
            report_url=rem.report_url(threat.platform),
            body=pt["body"],
            generator=pt_gen,
        ),
        safaricom_report=SafaricomReport(
            channel=channels["safaricom_channel"],
            to=channels["safaricom_to"],
            subject=sr["subject"],
            body=sr["body"],
            generator=sr_gen,
        ),
        kecirt_report=KecirtReport(
            to=channels["kecirt_to"], subject=kr["subject"], body=kr["body"], generator=kr_gen
        ),
        contacts_verified=rem.contacts_verified(),
    )
