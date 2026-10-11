"""Meta Rights Manager API integration for automated takedowns (TSK-038).

Spec: docs/BACKEND.md section 6.9 & future_spec.md section 2.1.

Capabilities:
1. Meta Rights Manager / Graph API client (https://graph.facebook.com/v19.0/...)
   submitting intellectual property / impersonation takedown notices.
2. Automated takedown trigger for verified clones exceeding the strict 95+ composite score threshold.
3. Resilient fallback to deterministic simulated takedown submission when META_ACCESS_TOKEN is unset,
   when running in DEMO_MODE, or when the feature is disabled, without leaking errors.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, Literal
from uuid import uuid4

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import log_event
from app.core.repository import Repository, utcnow
from app.engine.constants import META_TAKEDOWN_THRESHOLD
from app.schemas.remediation import RemediationCreate
from app.schemas.threat import ThreatRecord

log = logging.getLogger("halisi.meta_rights")

META_GRAPH_API_DEFAULT_URL: Final = "https://graph.facebook.com/v19.0"
DEFAULT_TIMEOUT: Final = 10.0


class MetaRightsManagerError(Exception):
    """Base exception for Meta Rights Manager API errors."""


@dataclass(slots=True)
class TakedownResult:
    """Outcome of a Meta Rights Manager takedown submission."""

    takedown_id: str
    status: Literal["submitted", "simulated"]
    timestamp: datetime
    threat_handle: str
    threat_url: str
    merchant_name: str
    score: float
    evidence_hash: str
    response_payload: dict[str, Any] | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        """True if the takedown was accepted or successfully simulated."""
        return self.status in ("submitted", "simulated") and self.error is None

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


def compute_evidence_hash(
    handle: str,
    url: str,
    score: float,
    avatar_phash: str | None = None,
    phones: list[str] | None = None,
    tills: list[str] | None = None,
) -> str:
    """Deterministic SHA-256 evidence bundle hash for chain-of-custody verification."""
    clean_phones = sorted(phones or [])
    clean_tills = sorted(tills or [])
    bundle = (
        f"{handle.strip().lower()}|{url.strip()}|{score:.2f}|"
        f"{avatar_phash or ''}|{','.join(clean_phones)}|{','.join(clean_tills)}"
    )
    return hashlib.sha256(bundle.encode("utf-8")).hexdigest()


def build_takedown_payload(
    threat_handle: str,
    threat_url: str,
    merchant_name: str,
    score: float,
    evidence_hash: str,
) -> dict[str, Any]:
    """Assemble the takedown request payload for Meta Graph API / Rights Manager."""
    clean_handle = threat_handle.strip().lstrip("@")
    return {
        "url": threat_url.strip(),
        "target_handle": clean_handle,
        "infringed_party": merchant_name.strip(),
        "claim_type": "brand_impersonation",
        "confidence_score": score,
        "evidence_bundle_hash": evidence_hash,
        "reason": (
            f"Automated impersonation takedown notice via Halisi AI detection system "
            f"(Forensic Score: {score:.1f}/100, Infringed Entity: {merchant_name})"
        ),
    }


class MetaRightsManagerClient:
    """Client for Meta Graph API / Rights Manager automated takedowns."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._http = http_client

    @property
    def is_configured(self) -> bool:
        """True if credentials are present, feature is enabled, and not in demo mode."""
        return (
            bool(self.settings.meta_access_token)
            and not self.settings.demo_mode
            and self.settings.meta_rights_manager_enabled
        )

    def get_endpoint_url(self) -> str:
        """Construct the Meta Graph API Rights Manager endpoint URL."""
        base = (self.settings.meta_graph_api_url or META_GRAPH_API_DEFAULT_URL).rstrip("/")
        rm_id = (self.settings.meta_rights_manager_id or "").strip()
        if rm_id:
            return f"{base}/{rm_id}/takedown_requests"
        return f"{base}/takedown_requests"

    async def submit_takedown(
        self,
        threat_handle: str,
        threat_url: str,
        merchant_name: str,
        score: float,
        evidence_hash: str,
    ) -> TakedownResult:
        """Submit an intellectual property / impersonation takedown notice to Meta.

        When unconfigured or in DEMO_MODE, returns a deterministic simulated record without network calls.
        """
        clean_handle = threat_handle.strip().lstrip("@")
        clean_url = threat_url.strip()
        now = utcnow()

        # Fallback to deterministic simulation if unconfigured, demo mode, or disabled
        if not self.is_configured:
            reason = (
                "demo_mode"
                if self.settings.demo_mode
                else ("disabled" if not self.settings.meta_rights_manager_enabled else "unconfigured")
            )
            seed = f"{merchant_name}:{clean_handle}:{evidence_hash}"
            sim_id = f"meta_sim_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"
            log_event(
                "meta_rights_takedown_simulated",
                threat_handle=clean_handle,
                merchant=merchant_name,
                score=score,
                takedown_id=sim_id,
                reason=reason,
            )
            return TakedownResult(
                takedown_id=sim_id,
                status="simulated",
                timestamp=now,
                threat_handle=clean_handle,
                threat_url=clean_url,
                merchant_name=merchant_name,
                score=score,
                evidence_hash=evidence_hash,
                response_payload={"simulated": True, "reason": reason},
            )

        endpoint = self.get_endpoint_url()
        headers = {
            "Authorization": f"Bearer {self.settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        payload = build_takedown_payload(
            threat_handle=clean_handle,
            threat_url=clean_url,
            merchant_name=merchant_name,
            score=score,
            evidence_hash=evidence_hash,
        )

        try:
            if self._http is not None:
                resp = await self._http.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.settings.meta_timeout_seconds,
                )
            else:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=self.settings.meta_timeout_seconds,
                    )
        except httpx.RequestError as exc:
            log_event("meta_rights_request_error", error=str(exc), handle=clean_handle)
            raise MetaRightsManagerError(f"Network error submitting takedown to Meta: {exc}") from exc

        if resp.status_code not in (200, 201):
            log_event(
                "meta_rights_api_error",
                status_code=resp.status_code,
                text=resp.text,
                handle=clean_handle,
            )
            raise MetaRightsManagerError(
                f"Meta Graph API error ({resp.status_code}): {resp.text}"
            )

        data: dict[str, Any] = resp.json() if resp.content else {}
        takedown_id = str(data.get("takedown_id") or data.get("id") or f"meta_tk_{uuid4().hex[:12]}")
        log_event(
            "meta_rights_takedown_submitted",
            threat_handle=clean_handle,
            merchant=merchant_name,
            score=score,
            takedown_id=takedown_id,
        )

        return TakedownResult(
            takedown_id=takedown_id,
            status="submitted",
            timestamp=now,
            threat_handle=clean_handle,
            threat_url=clean_url,
            merchant_name=merchant_name,
            score=score,
            evidence_hash=evidence_hash,
            response_payload=data,
        )


async def submit_takedown(
    threat_handle: str,
    threat_url: str,
    merchant_name: str,
    score: float,
    evidence_hash: str,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> TakedownResult:
    """Convenience functional wrapper around MetaRightsManagerClient.submit_takedown."""
    manager = MetaRightsManagerClient(settings=settings, http_client=client)
    return await manager.submit_takedown(
        threat_handle=threat_handle,
        threat_url=threat_url,
        merchant_name=merchant_name,
        score=score,
        evidence_hash=evidence_hash,
    )


async def maybe_submit_meta_takedown(
    repo: Repository,
    threat: ThreatRecord,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> TakedownResult | None:
    """Submit an automated Meta Rights Manager takedown if score is >= 95.0.

    When submitted or simulated:
    - Updates threat status to 'takedown_filed'
    - Logs remediation playbook record in repository
    Returns TakedownResult if submitted/simulated, or None if skipped.
    """
    cfg = settings or get_settings()
    if not cfg.meta_rights_manager_enabled:
        return None
    if threat.composite_score < META_TAKEDOWN_THRESHOLD:
        return None
    if threat.status in ("resolved", "false_positive", "takedown_filed"):
        return None

    merchant = await repo.get_merchant(threat.merchant_id)
    merchant_name = merchant.business_name if merchant else "Protected Brand"

    evidence_hash = compute_evidence_hash(
        handle=threat.target_handle,
        url=threat.target_url,
        score=threat.composite_score,
        avatar_phash=threat.avatar_phash,
        phones=threat.extracted_phones,
        tills=threat.extracted_tills,
    )

    manager = MetaRightsManagerClient(settings=cfg, http_client=client)
    result = await manager.submit_takedown(
        threat_handle=threat.target_handle,
        threat_url=threat.target_url,
        merchant_name=merchant_name,
        score=threat.composite_score,
        evidence_hash=evidence_hash,
    )

    if result.success:
        try:
            await repo.update_threat_status(threat.id, "takedown_filed")
        except Exception as exc:  # noqa: BLE001
            log_event(
                "meta_takedown_status_update_error",
                threat_id=str(threat.id),
                error=str(exc),
            )
        try:
            await repo.insert_remediation(
                RemediationCreate(
                    threat_id=threat.id,
                    playbook_type="platform_takedown",
                    language="en",
                    generated_content=(
                        f"Automated Meta Rights Manager takedown submitted for @{threat.target_handle}.\n"
                        f"Takedown ID: {result.takedown_id} | Status: {result.status}\n"
                        f"Evidence SHA-256: {evidence_hash}\n"
                        f"Timestamp: {result.timestamp.isoformat()}"
                    ),
                    generator="template",
                    dispatched_to="meta_rights_manager",
                )
            )
        except Exception as exc:  # noqa: BLE001
            log_event(
                "meta_takedown_remediation_log_error",
                threat_id=str(threat.id),
                error=str(exc),
            )

    return result
