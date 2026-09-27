"""The ``/check`` pipeline (docs/BACKEND.md section 2.1), shared by the API, the seeder and the simulator.

parse -> official short-circuit -> acquire profile (tier 1 known / tier 2 OpenGraph / tier 3 manual)
-> hash (+ CLIP) the avatar -> extract payment details -> ``score_against_all`` -> CheckResult
-> upsert the threat (>= threshold) -> scan + alerts (background).
"""

import asyncio
import base64
import binascii
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

import httpx

from app.alerts.dispatcher import dispatch_threat_alert
from app.core.cache import TTLCache
from app.core.config import Settings
from app.core.errors import InvalidImage, PaymentInput, TargetUnreachable, UnsupportedPlatform
from app.core.logging import log_event
from app.core.repository import Repository, utcnow
from app.core.security import Resolver, system_resolver
from app.engine import imaging
from app.engine.embeddings import ClipEmbedder
from app.engine.hasher import ImageFeatures, compute_hashes
from app.engine.payment import PaymentEvidence
from app.engine.scorer import (
    MerchantProfile,
    ScoreResult,
    ScoringContext,
    TargetProfile,
    safe_action,
    score_against_all,
)
from app.ingestion.extractors import extract_payment_evidence
from app.ingestion.page_scraper import FetchError, fetch_opengraph
from app.ingestion.url_parser import ParsedInput, UnsupportedInput, parse_input
from app.schemas.check import (
    CheckRequest,
    CheckResult,
    HashesOut,
    ManualInput,
    SafeActionOut,
    ScanCreate,
    TargetInfo,
    TargetProfileRecord,
)
from app.schemas.common import ScanSource
from app.schemas.merchant import MerchantRecord
from app.schemas.threat import ThreatRecord, ThreatUpsert
from app.services.serializers import matched_merchant, merchant_profile

MERCHANT_CACHE_SECONDS = 60.0


@dataclass(slots=True)
class Acquired:
    """Page data from whichever tier answered, with the avatar already hashed."""

    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    avatar: ImageFeatures | None = None
    follower_count: int | None = None
    post_count: int | None = None
    account_created_on: date | None = None
    fetched_via: str = "none"
    url: str | None = None


@dataclass(slots=True)
class CheckOutcome:
    """Everything one check produced. ``persist`` writes the scan and alerts (run it in the background)."""

    result: CheckResult
    scan: ScanCreate
    threat_before: ThreatRecord | None = None
    threat_after: ThreatRecord | None = None
    score: ScoreResult | None = None
    evidence: PaymentEvidence = field(default_factory=PaymentEvidence)


class MerchantCache:
    """Merchant records + engine profiles, refreshed every minute or when invalidated (onboarding)."""

    def __init__(self, repo: Repository, ttl: float = MERCHANT_CACHE_SECONDS) -> None:
        self.repo = repo
        self.ttl = ttl
        self._loaded_at = 0.0
        self._records: list[MerchantRecord] = []
        self._profiles: list[MerchantProfile] = []
        self._lock = asyncio.Lock()

    def invalidate(self) -> None:
        """Force a reload on the next access."""
        self._loaded_at = 0.0

    async def get(self) -> tuple[list[MerchantRecord], list[MerchantProfile]]:
        """(records, profiles), reloading when stale."""
        async with self._lock:
            if time.monotonic() - self._loaded_at > self.ttl:
                self._records = await self.repo.list_merchants()
                self._profiles = [merchant_profile(r) for r in self._records]
                self._loaded_at = time.monotonic()
            return self._records, self._profiles

    async def by_id(self, merchant_id: str) -> MerchantRecord | None:
        """Cached record by id."""
        records, _ = await self.get()
        return next((r for r in records if str(r.id) == merchant_id), None)


def decode_avatar(data_b64: str) -> bytes:
    """Decode a (data-URL or plain) base64 avatar. Raises InvalidImage."""
    payload = data_b64.split(",", 1)[1] if data_b64.startswith("data:") else data_b64
    try:
        return base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise InvalidImage("The uploaded picture is not valid base64.") from exc


class CheckService:
    """Runs checks. One instance per app (holds the HTTP client, CLIP model and caches)."""

    def __init__(
        self,
        repo: Repository,
        settings: Settings,
        http: httpx.AsyncClient,
        clip: ClipEmbedder,
        *,
        resolver: Resolver = system_resolver,
    ) -> None:
        self.repo = repo
        self.settings = settings
        self.http = http
        self.clip = clip
        self.resolver = resolver
        self.merchants = MerchantCache(repo)
        self.fetched: TTLCache[Acquired] = TTLCache(ttl_seconds=settings.profile_cache_seconds)

    # -- image features --------------------------------------------------------------------
    async def features_from_bytes(self, data: bytes) -> ImageFeatures:
        """Normalise + hash (+ embed) image bytes off the event loop. Raises InvalidImage."""
        try:
            image = await asyncio.to_thread(imaging.normalize_image, data)
        except imaging.InvalidImage as exc:
            raise InvalidImage(str(exc)) from exc
        hashes = await asyncio.to_thread(compute_hashes, image)
        embedding = await self.clip.embed_async(image)
        return ImageFeatures(phash=hashes.phash, dhash=hashes.dhash, embedding=embedding)

    # -- acquisition -----------------------------------------------------------------------
    async def acquire(self, parsed: ParsedInput, manual: ManualInput | None) -> Acquired:
        """Tier 3 (manual) if given, else tier 1 (known), else tier 2 (OpenGraph).

        Raises TargetUnreachable.
        """
        assert parsed.platform and parsed.handle
        if manual is not None:
            avatar = (
                await self.features_from_bytes(decode_avatar(manual.avatar_base64))
                if manual.avatar_base64
                else None
            )
            return Acquired(
                display_name=manual.display_name,
                bio=manual.bio,
                avatar=avatar,
                fetched_via="manual",
                url=parsed.url,
            )

        known = await self.repo.get_target_profile(parsed.platform, parsed.handle)
        if known is not None and (known.fetched_via == "seed" or self._fresh(known.fetched_at)):
            avatar = None
            if known.avatar_phash and known.avatar_dhash:
                avatar = ImageFeatures(
                    known.avatar_phash.strip(), known.avatar_dhash.strip(), known.avatar_embedding
                )
            return Acquired(
                display_name=known.display_name,
                bio=known.bio,
                avatar_url=known.avatar_url,
                avatar=avatar,
                follower_count=known.follower_count,
                post_count=known.post_count,
                account_created_on=known.account_created_on,
                fetched_via="seed" if known.fetched_via == "seed" else "opengraph",
                url=known.url or parsed.url,
            )

        key = f"{parsed.platform}:{parsed.handle}"
        cached = self.fetched.get(key)
        if cached is not None:
            return cached
        if self.settings.demo_mode or not self.settings.scraper_enabled or not parsed.url:
            raise TargetUnreachable()
        try:
            page = await fetch_opengraph(
                self.http,
                parsed.url,
                parsed.platform,
                parsed.handle,
                timeout=self.settings.fetch_timeout_seconds,
                image_timeout=self.settings.image_timeout_seconds,
                resolver=self.resolver,
            )
        except FetchError as exc:
            log_event("fetch_failed", platform=parsed.platform, reason=exc.reason, status=exc.status_code)
            raise TargetUnreachable() from exc
        avatar = None
        if page.avatar_bytes:
            try:
                avatar = await self.features_from_bytes(page.avatar_bytes)
            except InvalidImage:
                avatar = None
        acquired = Acquired(
            display_name=page.display_name,
            bio=page.bio,
            avatar_url=page.avatar_url,
            avatar=avatar,
            follower_count=page.follower_count,
            post_count=page.post_count,
            fetched_via="opengraph",
            url=parsed.url,
        )
        self.fetched.set(key, acquired)
        await self.repo.upsert_target_profile(
            TargetProfileRecord(
                platform=parsed.platform,
                handle=parsed.handle,
                url=parsed.url,
                display_name=page.display_name,
                bio=page.bio,
                avatar_url=page.avatar_url,
                avatar_phash=avatar.phash if avatar else None,
                avatar_dhash=avatar.dhash if avatar else None,
                avatar_embedding=list(avatar.embedding) if avatar and avatar.embedding else None,
                follower_count=page.follower_count,
                post_count=page.post_count,
                fetched_via="opengraph",
                fetched_at=utcnow(),
            )
        )
        return acquired

    def _fresh(self, fetched_at: datetime) -> bool:
        return (utcnow() - fetched_at).total_seconds() < self.settings.profile_cache_seconds

    # -- the check -------------------------------------------------------------------------
    async def check(
        self,
        request: CheckRequest,
        *,
        source: ScanSource = "public_checker",
        scan_id: UUID | None = None,
        now: datetime | None = None,
        acquired: Acquired | None = None,
    ) -> CheckOutcome:
        """Run one check and upsert the threat. Call :meth:`persist` afterwards for the scan + alerts.

        ``acquired`` bypasses the tiers (simulator: a synthetic page built in memory).
        Raises UnsupportedPlatform, PaymentInput, TargetUnreachable, InvalidImage.
        """
        started = time.perf_counter()
        now = now or utcnow()
        try:
            parsed = parse_input(request.url or request.handle or "", request.platform)
        except UnsupportedInput as exc:
            raise UnsupportedPlatform(str(exc)) from exc
        if parsed.is_payment:
            raise PaymentInput()
        assert parsed.platform and parsed.handle

        records, profiles = await self.merchants.get()
        scan_id = scan_id or uuid4()

        official = (
            None
            if acquired is not None
            else await self.repo.find_official_handle(parsed.platform, parsed.handle)
        )
        if official is not None:
            result = self._official_result(scan_id, parsed, official, started)
            return CheckOutcome(
                result=result, scan=self._scan(parsed, result, source, official.id, None, now)
            )

        page = acquired or await self.acquire(parsed, request.manual)
        text = " \n".join(t for t in (page.display_name, page.bio) if t)
        evidence = extract_payment_evidence(text)
        target = TargetProfile(
            platform=parsed.platform,
            handle=parsed.handle,
            display_name=page.display_name,
            bio=page.bio,
            avatar=page.avatar,
            payment=evidence,
            follower_count=page.follower_count,
            post_count=page.post_count,
            account_created_on=page.account_created_on,
        )
        ctx = ScoringContext(
            today=now.date(),
            confirmed_reported=await self.repo.confirmed_reported_numbers(),
            threat_threshold=self.settings.threat_threshold,
            suspicious_threshold=self.settings.suspicious_threshold,
        )
        score = score_against_all(target, profiles, ctx)
        record = next((r for r in records if score.merchant and str(r.id) == score.merchant.id), None)

        before = after = None
        if record is not None and score.score >= self.settings.threat_threshold:
            before = await self.repo.get_threat_by_target(record.id, parsed.platform, parsed.handle)
            after = await self.repo.upsert_threat(
                self._threat_upsert(parsed, page, evidence, score, record, source, now)
            )

        result = self._scored_result(scan_id, parsed, page, score, record, after, started)
        scan = self._scan(
            parsed, result, source, record.id if record else None, after.id if after else None, now
        )
        log_event(
            "check",
            scan_id=str(scan_id),
            verdict=result.verdict,
            score=result.score,
            platform=parsed.platform,
            fetched_via=page.fetched_via,
            elapsed_ms=result.elapsed_ms,
        )
        return CheckOutcome(
            result=result, scan=scan, threat_before=before, threat_after=after, score=score, evidence=evidence
        )

    async def persist(self, outcome: CheckOutcome) -> None:
        """Insert the scan and dispatch the in-app alert (safe to run as a BackgroundTask)."""
        await self.repo.insert_scan(outcome.scan)
        if outcome.threat_after is not None:
            await dispatch_threat_alert(
                self.repo,
                outcome.threat_before,
                outcome.threat_after,
                threshold=self.settings.threat_threshold,
                dedup_hours=self.settings.alert_dedup_hours,
                now=outcome.scan.created_at,
            )

    # -- builders --------------------------------------------------------------------------
    def _elapsed(self, started: float) -> int:
        return max(0, int(round((time.perf_counter() - started) * 1000)))

    def _target_info(self, parsed: ParsedInput, page: Acquired | None) -> TargetInfo:
        page = page or Acquired()
        return TargetInfo(
            platform=parsed.platform,
            handle=parsed.handle,
            display_name=page.display_name,
            url=page.url or parsed.url,
            avatar_url=page.avatar_url,
            follower_count=page.follower_count,
            post_count=page.post_count,
            account_created_on=page.account_created_on,
            fetched_via=page.fetched_via,  # type: ignore[arg-type]
        )

    def _official_result(
        self, scan_id: UUID, parsed: ParsedInput, merchant: MerchantRecord, started: float
    ) -> CheckResult:
        en, sw = safe_action(merchant_profile(merchant), parsed.platform)
        return CheckResult(
            scan_id=scan_id,
            verdict="official",
            score=0.0,
            confidence=1.0,
            target=self._target_info(parsed, None),
            matched_merchant=matched_merchant(merchant),
            dimensions=[],
            reasons=[],
            hashes=None,
            safe_action=SafeActionOut(text=en, text_sw=sw),
            threat_id=None,
            elapsed_ms=self._elapsed(started),
        )

    def _scored_result(
        self,
        scan_id: UUID,
        parsed: ParsedInput,
        page: Acquired,
        score: ScoreResult,
        record: MerchantRecord | None,
        threat: ThreatRecord | None,
        started: float,
    ) -> CheckResult:
        hashes = None
        if score.visual is not None and page.avatar is not None and record is not None:
            hashes = HashesOut(
                target_phash=page.avatar.phash,
                reference_phash=record.logo_phash,
                hamming_distance=score.visual.phash_distance,
            )
        safe = None
        if score.merchant is not None:
            en, sw = safe_action(score.merchant, parsed.platform)
            safe = SafeActionOut(text=en, text_sw=sw)
        return CheckResult.model_validate(
            {
                "scan_id": scan_id,
                "verdict": score.verdict,
                "score": score.score,
                "confidence": score.confidence,
                "target": self._target_info(parsed, page),
                "matched_merchant": matched_merchant(record) if record else None,
                "dimensions": score.dimensions_payload(),
                "reasons": score.reasons_payload(),
                "hashes": hashes,
                "safe_action": safe,
                "threat_id": threat.id if threat else None,
                "elapsed_ms": self._elapsed(started),
            }
        )

    def _threat_upsert(
        self,
        parsed: ParsedInput,
        page: Acquired,
        evidence: PaymentEvidence,
        score: ScoreResult,
        record: MerchantRecord,
        source: ScanSource,
        now: datetime,
    ) -> ThreatUpsert:
        dims = {d.key: d.score for d in score.dimensions}
        return ThreatUpsert(
            merchant_id=record.id,
            platform=parsed.platform or "",
            target_handle=parsed.handle or "",
            target_url=page.url or parsed.url or "",
            display_name=page.display_name,
            bio=page.bio,
            avatar_url=page.avatar_url,
            avatar_phash=page.avatar.phash if page.avatar else None,
            avatar_dhash=page.avatar.dhash if page.avatar else None,
            avatar_embedding=list(page.avatar.embedding) if page.avatar and page.avatar.embedding else None,
            account_created_on=page.account_created_on,
            follower_count=page.follower_count,
            post_count=page.post_count,
            extracted_phones=list(evidence.phones),
            extracted_tills=list(evidence.tills),
            visual_score=dims.get("visual"),
            identity_score=dims.get("identity"),
            payment_score=dims.get("payment"),
            language_score=dims.get("language"),
            account_score=dims.get("account"),
            composite_score=score.score,
            confidence=score.confidence,
            reasons=score.reasons_payload(),
            source=source,
            seen_at=now,
        )

    def _scan(
        self,
        parsed: ParsedInput,
        result: CheckResult,
        source: ScanSource,
        merchant_id: UUID | None,
        threat_id: UUID | None,
        now: datetime,
    ) -> ScanCreate:
        return ScanCreate(
            id=result.scan_id,
            input_value=parsed.value[:2048],
            input_kind=parsed.kind,
            platform=parsed.platform,
            target_handle=parsed.handle,
            source=source,
            verdict=result.verdict,
            composite_score=result.score,
            merchant_id=merchant_id,
            threat_id=threat_id,
            result=result.model_dump(mode="json"),
            elapsed_ms=result.elapsed_ms,
            created_at=now,
        )


BackgroundRunner = Callable[[CheckOutcome], Awaitable[None]]
