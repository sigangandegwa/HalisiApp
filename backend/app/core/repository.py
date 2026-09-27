"""Repository layer (docs/BACKEND.md section 4): one protocol, two implementations.

* ``MemoryRepository``: dict-backed, used in ``DEMO_MODE`` and tests (seeded by ``mock_seeder``).
* ``SupabaseRepository``: supabase-py (synchronous) wrapped in ``asyncio.to_thread``.

Both must pass the same tests (``tests/core/test_repository.py``). Business rules that don't need
a database (stats, payment matching, status transitions) live in pure helpers here so the two
implementations can't drift.
"""

import asyncio
import json
import statistics
import uuid
from collections import Counter
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from app.engine.payment import canonical_phone, canonical_till
from app.schemas.alert import AlertCreate, AlertRecord
from app.schemas.check import ScanCreate, ScanRecord, TargetProfileRecord
from app.schemas.merchant import LogoFeatures, MerchantCreate, MerchantHandle, MerchantRecord
from app.schemas.remediation import RemediationCreate, RemediationRecord
from app.schemas.report import PaymentLookup, PlatformCount, ReportCreate, ReportRecord, Stats
from app.schemas.threat import StatusEvent, ThreatRecord, ThreatUpsert

INACTIVE_STATUSES = frozenset({"resolved", "false_positive"})
WARNING_VERDICTS = frozenset({"impersonation", "suspicious"})


class RepositoryError(Exception):
    """Base class for repository failures."""


class NotFound(RepositoryError):
    """The referenced row does not exist."""


class Conflict(RepositoryError):
    """A unique constraint would be violated (``code`` says which)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@runtime_checkable
class Repository(Protocol):
    """Data access used by the API. All methods are async; implementations must not block the loop."""

    async def ping(self) -> str: ...
    async def list_merchants(self) -> list[MerchantRecord]: ...
    async def get_merchant(self, merchant_id: UUID) -> MerchantRecord | None: ...
    async def get_merchant_by_slug(self, slug: str) -> MerchantRecord | None: ...
    async def find_official_handle(self, platform: str, handle: str) -> MerchantRecord | None: ...
    async def find_by_payment(self, phone: str | None, till: str | None) -> PaymentLookup: ...
    async def create_merchant(
        self,
        data: MerchantCreate,
        hashes: LogoFeatures,
        *,
        logo_url: str | None = None,
        merchant_id: UUID | None = None,
        is_verified: bool = True,
        created_at: datetime | None = None,
    ) -> MerchantRecord: ...
    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord: ...
    async def get_threat_by_target(
        self, merchant_id: UUID, platform: str, handle: str
    ) -> ThreatRecord | None: ...
    async def list_threats(self, merchant_id: UUID, status: str | None) -> list[ThreatRecord]: ...
    async def list_threats_by_status(self, statuses: Sequence[str]) -> list[ThreatRecord]: ...
    async def get_threat(self, threat_id: UUID) -> ThreatRecord | None: ...
    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord: ...
    async def insert_scan(self, scan: ScanCreate) -> UUID: ...
    async def get_scan(self, scan_id: UUID) -> ScanRecord | None: ...
    async def latest_scan_for_threat(self, threat_id: UUID) -> ScanRecord | None: ...
    async def insert_remediation(self, log: RemediationCreate) -> None: ...
    async def list_remediations(self, threat_id: UUID) -> list[RemediationRecord]: ...
    async def insert_report(
        self,
        report: ReportCreate,
        *,
        report_id: UUID | None = None,
        status: str = "pending",
        threat_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> UUID: ...
    async def set_report_status(self, report_id: UUID, status: str) -> None: ...
    async def confirmed_reported_numbers(self) -> frozenset[str]: ...
    async def insert_alert(self, alert: AlertCreate) -> AlertRecord: ...
    async def last_alert_for_threat(self, threat_id: UUID) -> AlertRecord | None: ...
    async def list_alerts(
        self, merchant_id: UUID, since: datetime | None, unread_only: bool, limit: int
    ) -> list[AlertRecord]: ...
    async def unread_count(self, merchant_id: UUID) -> int: ...
    async def mark_alerts_read(self, merchant_id: UUID, ids: list[UUID] | None) -> int: ...
    async def get_target_profile(self, platform: str, handle: str) -> TargetProfileRecord | None: ...
    async def upsert_target_profile(self, profile: TargetProfileRecord) -> None: ...
    async def stats(self, merchant_id: UUID | None) -> Stats: ...


# --- pure helpers shared by both implementations -----------------------------------------------

THREAT_NAMESPACE = uuid.UUID("5b0f2a52-8f2e-4d1e-9a51-1f3c9b8e7a10")


_last_now: datetime | None = None


def utcnow() -> datetime:
    """Timezone-aware now (UTC), strictly increasing within the process.

    Windows clocks can return the same value for calls a few ms apart. The alert polling cursor is
    ``created_at > since``, so two equal timestamps would hide an alert; bumping by 1 us prevents that.
    """
    global _last_now
    now = datetime.now(UTC)
    if _last_now is not None and now <= _last_now:
        now = _last_now + timedelta(microseconds=1)
    _last_now = now
    return now


def threat_id_for(merchant_id: UUID, platform: str, handle: str) -> UUID:
    """Deterministic threat id from its natural key (merchant, platform, handle): idempotent upserts."""
    p, h = _handle_key(platform, handle)
    return uuid.uuid5(THREAT_NAMESPACE, f"{merchant_id}:{p}:{h}")


def canonical_number(value: str | None) -> str | None:
    """A phone as E.164 or a till/paybill as digits, else None."""
    if not value:
        return None
    return canonical_phone(value) or canonical_till(value)


def merchant_numbers(merchant: MerchantRecord) -> set[str]:
    """Every canonical phone/till registered to a merchant."""
    values = [*merchant.phone_numbers, merchant.mpesa_number or ""]
    return {n for n in map(canonical_number, values) if n}


def build_merchant(
    data: MerchantCreate,
    hashes: LogoFeatures,
    *,
    logo_url: str | None,
    merchant_id: UUID | None,
    is_verified: bool,
    created_at: datetime | None,
) -> MerchantRecord:
    """Assemble a new MerchantRecord from onboarding data (numbers canonicalised)."""
    now = created_at or utcnow()
    phones = [p for p in (canonical_phone(n) for n in data.phone_numbers) if p]
    number = data.mpesa_number
    if number:
        number = canonical_phone(number) if data.mpesa_type == "pochi" else canonical_till(number) or number
    handles = [
        MerchantHandle(
            platform=h.platform, handle=h.handle, url=h.url or default_profile_url(h.platform, h.handle)
        )
        for h in data.handles
    ]
    return MerchantRecord(
        id=merchant_id or uuid.uuid4(),
        business_name=data.business_name,
        slug=data.slug,
        aliases=data.aliases,
        category=data.category,
        location=data.location,
        established_on=data.established_on,
        logo_url=logo_url,
        logo_phash=hashes.phash,
        logo_dhash=hashes.dhash,
        logo_embedding=hashes.embedding,
        mpesa_type=data.mpesa_type,
        mpesa_number=number,
        mpesa_account_name=data.mpesa_account_name,
        phone_numbers=list(dict.fromkeys(phones)),
        is_verified=is_verified,
        created_at=now,
        updated_at=now,
        official_handles=handles,
    )


def default_profile_url(platform: str, handle: str) -> str | None:
    """Canonical public URL of a handle on a platform."""
    return {
        "instagram": f"https://instagram.com/{handle}",
        "facebook": f"https://facebook.com/{handle}",
        "tiktok": f"https://tiktok.com/@{handle}",
        "x": f"https://x.com/{handle}",
    }.get(platform)


def merge_threat(existing: ThreatRecord | None, upsert: ThreatUpsert, now: datetime) -> ThreatRecord:
    """Insert-or-update semantics for threats.

    New threats start ``detected``. A re-check updates scores and profile data but keeps the
    workflow status, except that a ``resolved`` page that is seen again goes back to ``detected``.
    """
    seen = upsert.seen_at or now
    fields = upsert.model_dump(exclude={"id", "seen_at"})
    if existing is None:
        new_id = upsert.id or threat_id_for(upsert.merchant_id, upsert.platform, upsert.target_handle)
        return ThreatRecord(
            id=new_id,
            **fields,
            status="detected",
            status_history=[StatusEvent(status="detected", at=seen)],
            first_seen_at=seen,
            last_checked_at=seen,
        )
    status, history, resolved_at = existing.status, list(existing.status_history), existing.resolved_at
    if status == "resolved":
        status, resolved_at = "detected", None
        history.append(StatusEvent(status="detected", at=seen))
    return existing.model_copy(
        update={
            **fields,
            "status": status,
            "status_history": history,
            "resolved_at": resolved_at,
            "source": existing.source,
            "last_checked_at": seen,
        }
    )


def apply_status(threat: ThreatRecord, status: str, now: datetime) -> ThreatRecord:
    """Return ``threat`` moved to ``status`` with history and ``resolved_at`` maintained."""
    if status == threat.status:
        return threat
    history = [*threat.status_history, StatusEvent(status=status, at=now)]  # type: ignore[arg-type]
    resolved_at = now if status == "resolved" else None
    return threat.model_copy(update={"status": status, "status_history": history, "resolved_at": resolved_at})


def payment_lookup(
    number: str,
    merchants: Iterable[MerchantRecord],
    reports: Iterable[ReportRecord],
    threats: Iterable[ThreatRecord],
) -> PaymentLookup:
    """Facts about one canonical phone/till across merchants, reports and active threats."""
    merchant = next((m for m in merchants if number in merchant_numbers(m)), None)
    matching = [
        r
        for r in reports
        if r.status != "rejected"
        and number in {canonical_number(r.reported_phone), canonical_number(r.reported_till)}
    ]
    linked = [
        t
        for t in threats
        if t.status not in INACTIVE_STATUSES
        and number in {n for n in map(canonical_number, [*t.extracted_phones, *t.extracted_tills]) if n}
    ]
    return PaymentLookup(
        merchant=merchant,
        report_count=len(matching),
        confirmed_reports=sum(1 for r in matching if r.status == "confirmed"),
        linked_threats=len(linked),
    )


def compute_stats(
    merchants: Sequence[MerchantRecord],
    threats: Sequence[ThreatRecord],
    scans: Sequence[ScanRecord],
    merchant_id: UUID | None,
    now: datetime,
) -> Stats:
    """KPIs (section 5.9). Every number is a count over stored rows; nothing is estimated or invented.

    ``customers_warned_estimate`` counts real public checks (not seed/simulator scans) that warned a
    user (impersonation or suspicious) about a page imitating this merchant.
    """
    if merchant_id is not None:
        threats = [t for t in threats if t.merchant_id == merchant_id]
        scans = [s for s in scans if s.merchant_id == merchant_id]
    live_threats = [t for t in threats if t.status != "false_positive"]
    week_ago = now - timedelta(days=7)
    elapsed = [s.elapsed_ms for s in scans if s.elapsed_ms is not None]
    platforms = Counter(t.platform for t in live_threats).most_common()
    stats = Stats(
        pages_scanned=len(scans),
        threats_detected=len(live_threats),
        impersonations_blocked_7d=sum(
            1 for s in scans if s.verdict == "impersonation" and s.created_at >= week_ago
        ),
        merchants_protected=sum(1 for m in merchants if m.is_verified),
        median_detection_ms=int(statistics.median(elapsed)) if elapsed else 0,
        top_platforms=[PlatformCount(platform=p, count=c) for p, c in platforms],
    )
    if merchant_id is not None:
        stats.active_threats = sum(1 for t in threats if t.status not in INACTIVE_STATUSES)
        stats.resolved = sum(1 for t in threats if t.status == "resolved")
        stats.customers_warned_estimate = sum(
            1 for s in scans if s.verdict in WARNING_VERDICTS and s.source == "public_checker"
        )
    return stats


def _handle_key(platform: str, handle: str) -> tuple[str, str]:
    return platform.lower(), handle.strip().lower().lstrip("@").rstrip("/")


# --- in-memory implementation ------------------------------------------------------------------


class MemoryRepository:
    """Dict-backed repository for ``DEMO_MODE`` and tests. Not thread-safe (single event loop)."""

    def __init__(self) -> None:
        self.merchants: dict[UUID, MerchantRecord] = {}
        self.threats: dict[UUID, ThreatRecord] = {}
        self.scans: dict[UUID, ScanRecord] = {}
        self.remediations: list[RemediationRecord] = []
        self.reports: dict[UUID, ReportRecord] = {}
        self.alerts: dict[UUID, AlertRecord] = {}
        self.profiles: dict[tuple[str, str], TargetProfileRecord] = {}

    async def ping(self) -> str:
        """Always healthy."""
        return "memory"

    async def list_merchants(self) -> list[MerchantRecord]:
        """All merchants, oldest first."""
        return sorted(self.merchants.values(), key=lambda m: (m.created_at, m.slug))

    async def get_merchant(self, merchant_id: UUID) -> MerchantRecord | None:
        """Merchant by id."""
        return self.merchants.get(merchant_id)

    async def get_merchant_by_slug(self, slug: str) -> MerchantRecord | None:
        """Merchant by public slug."""
        return next((m for m in self.merchants.values() if m.slug == slug), None)

    async def find_official_handle(self, platform: str, handle: str) -> MerchantRecord | None:
        """Exact official handle (lowercase, no '@', no trailing '/') on the same platform."""
        key = _handle_key(platform, handle)
        for merchant in self.merchants.values():
            if any(_handle_key(h.platform, h.handle) == key for h in merchant.official_handles):
                return merchant
        return None

    async def find_by_payment(self, phone: str | None, till: str | None) -> PaymentLookup:
        """Facts about a phone or till."""
        number = canonical_number(phone) or canonical_number(till)
        if number is None:
            return PaymentLookup()
        return payment_lookup(number, self.merchants.values(), self.reports.values(), self.threats.values())

    async def create_merchant(
        self,
        data: MerchantCreate,
        hashes: LogoFeatures,
        *,
        logo_url: str | None = None,
        merchant_id: UUID | None = None,
        is_verified: bool = True,
        created_at: datetime | None = None,
    ) -> MerchantRecord:
        """Insert a merchant (idempotent for the same id). Raises Conflict on slug/handle clashes."""
        record = build_merchant(
            data,
            hashes,
            logo_url=logo_url,
            merchant_id=merchant_id,
            is_verified=is_verified,
            created_at=created_at,
        )
        for other in self.merchants.values():
            if other.id == record.id:
                continue
            if other.slug == record.slug:
                raise Conflict("SLUG_TAKEN", f"Slug '{record.slug}' is already registered.")
            taken = {_handle_key(h.platform, h.handle) for h in other.official_handles}
            if any(_handle_key(h.platform, h.handle) in taken for h in record.official_handles):
                raise Conflict(
                    "HANDLE_TAKEN", "One of these handles is already registered to another merchant."
                )
        self.merchants[record.id] = record
        return record

    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord:
        """Insert or update on (merchant_id, platform, target_handle)."""
        existing = await self.get_threat_by_target(threat.merchant_id, threat.platform, threat.target_handle)
        record = merge_threat(existing, threat, utcnow())
        self.threats[record.id] = record
        return record

    async def get_threat_by_target(
        self, merchant_id: UUID, platform: str, handle: str
    ) -> ThreatRecord | None:
        """The threat for one page against one merchant."""
        key = _handle_key(platform, handle)
        return next(
            (
                t
                for t in self.threats.values()
                if t.merchant_id == merchant_id and _handle_key(t.platform, t.target_handle) == key
            ),
            None,
        )

    async def list_threats(self, merchant_id: UUID, status: str | None) -> list[ThreatRecord]:
        """A merchant's threats, highest score first."""
        rows = [
            t
            for t in self.threats.values()
            if t.merchant_id == merchant_id and (not status or t.status == status)
        ]
        return sorted(rows, key=lambda t: (-t.composite_score, t.first_seen_at))

    async def list_threats_by_status(self, statuses: Sequence[str]) -> list[ThreatRecord]:
        """Threats in any of ``statuses`` (takedown tracker)."""
        return [t for t in self.threats.values() if t.status in statuses]

    async def get_threat(self, threat_id: UUID) -> ThreatRecord | None:
        """Threat by id."""
        return self.threats.get(threat_id)

    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord:
        """Move a threat to ``status``. Raises NotFound."""
        threat = self.threats.get(threat_id)
        if threat is None:
            raise NotFound(f"Threat {threat_id} not found.")
        updated = apply_status(threat, status, utcnow())
        self.threats[threat_id] = updated
        return updated

    async def insert_scan(self, scan: ScanCreate) -> UUID:
        """Store a scan (idempotent for the same id)."""
        record = ScanRecord(
            **{**scan.model_dump(), "id": scan.id or uuid.uuid4(), "created_at": scan.created_at or utcnow()}
        )
        self.scans[record.id] = record
        return record.id

    async def get_scan(self, scan_id: UUID) -> ScanRecord | None:
        """Scan by id."""
        return self.scans.get(scan_id)

    async def latest_scan_for_threat(self, threat_id: UUID) -> ScanRecord | None:
        """Most recent scan linked to a threat."""
        rows = [s for s in self.scans.values() if s.threat_id == threat_id]
        return max(rows, key=lambda s: s.created_at, default=None)

    async def insert_remediation(self, log: RemediationCreate) -> None:
        """Append a remediation log row."""
        self.remediations.append(RemediationRecord(**log.model_dump(), id=uuid.uuid4(), created_at=utcnow()))

    async def list_remediations(self, threat_id: UUID) -> list[RemediationRecord]:
        """A threat's generated playbooks, oldest first."""
        return [r for r in self.remediations if r.threat_id == threat_id]

    async def insert_report(
        self,
        report: ReportCreate,
        *,
        report_id: UUID | None = None,
        status: str = "pending",
        threat_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> UUID:
        """Store a community report (numbers canonicalised)."""
        record = _report_record(report, report_id, status, threat_id, created_at)
        self.reports[record.id] = record
        return record.id

    async def set_report_status(self, report_id: UUID, status: str) -> None:
        """Moderation: confirm or reject a report. Raises NotFound."""
        report = self.reports.get(report_id)
        if report is None:
            raise NotFound(f"Report {report_id} not found.")
        self.reports[report_id] = report.model_copy(update={"status": status})

    async def confirmed_reported_numbers(self) -> frozenset[str]:
        """Canonical phones/tills from confirmed reports (feeds ScoringContext / override O3)."""
        return _confirmed_numbers(self.reports.values())

    async def insert_alert(self, alert: AlertCreate) -> AlertRecord:
        """Store an alert."""
        record = AlertRecord(
            **{
                **alert.model_dump(),
                "id": alert.id or uuid.uuid4(),
                "created_at": alert.created_at or utcnow(),
            }
        )
        self.alerts[record.id] = record
        return record

    async def last_alert_for_threat(self, threat_id: UUID) -> AlertRecord | None:
        """Most recent alert for a threat (de-duplication)."""
        rows = [a for a in self.alerts.values() if a.threat_id == threat_id]
        return max(rows, key=lambda a: a.created_at, default=None)

    async def list_alerts(
        self, merchant_id: UUID, since: datetime | None, unread_only: bool, limit: int
    ) -> list[AlertRecord]:
        """Alerts newer than ``since`` (exclusive), newest first."""
        rows = [
            a
            for a in self.alerts.values()
            if a.merchant_id == merchant_id
            and (since is None or a.created_at > since)
            and (not unread_only or a.read_at is None)
        ]
        return sorted(rows, key=lambda a: a.created_at, reverse=True)[:limit]

    async def unread_count(self, merchant_id: UUID) -> int:
        """Number of unread alerts."""
        return sum(1 for a in self.alerts.values() if a.merchant_id == merchant_id and a.read_at is None)

    async def mark_alerts_read(self, merchant_id: UUID, ids: list[UUID] | None) -> int:
        """Mark ``ids`` (or all when None) read; returns the remaining unread count."""
        now = utcnow()
        wanted = None if ids is None else set(ids)
        for alert_id, alert in list(self.alerts.items()):
            if (
                alert.merchant_id == merchant_id
                and alert.read_at is None
                and (wanted is None or alert_id in wanted)
            ):
                self.alerts[alert_id] = alert.model_copy(update={"read_at": now})
        return await self.unread_count(merchant_id)

    async def get_target_profile(self, platform: str, handle: str) -> TargetProfileRecord | None:
        """Tier-1 known page."""
        return self.profiles.get(_handle_key(platform, handle))

    async def upsert_target_profile(self, profile: TargetProfileRecord) -> None:
        """Store a seeded or OpenGraph-fetched page profile."""
        self.profiles[_handle_key(profile.platform, profile.handle)] = profile

    async def stats(self, merchant_id: UUID | None) -> Stats:
        """KPIs over stored rows."""
        return compute_stats(
            list(self.merchants.values()),
            list(self.threats.values()),
            list(self.scans.values()),
            merchant_id,
            utcnow(),
        )


def _report_record(
    report: ReportCreate,
    report_id: UUID | None,
    status: str,
    threat_id: UUID | None,
    created_at: datetime | None,
) -> ReportRecord:
    """Build a ReportRecord with canonical phone/till."""
    data = report.model_dump()
    data["reported_phone"] = canonical_phone(report.reported_phone or "") or report.reported_phone
    data["reported_till"] = canonical_till(report.reported_till or "") or report.reported_till
    if data["target_handle"]:
        data["target_handle"] = data["target_handle"].strip().lower().lstrip("@").rstrip("/")
    return ReportRecord(
        **data,
        id=report_id or uuid.uuid4(),
        status=status,
        threat_id=threat_id,
        created_at=created_at or utcnow(),
    )


def _confirmed_numbers(reports: Iterable[ReportRecord]) -> frozenset[str]:
    out: set[str] = set()
    for r in reports:
        if r.status == "confirmed":
            out.update(
                n for n in (canonical_number(r.reported_phone), canonical_number(r.reported_till)) if n
            )
    return frozenset(out)


# --- Supabase implementation -------------------------------------------------------------------


def _vector(value: Sequence[float] | None) -> str | None:
    """pgvector literal for PostgREST."""
    return None if value is None else "[" + ",".join(f"{v:.7g}" for v in value) + "]"


def _parse_vector(value: Any) -> list[float] | None:
    """PostgREST returns vectors as '[0.1,...]' strings."""
    if value is None or isinstance(value, list):
        return value
    return [float(v) for v in json.loads(value)]


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


class SupabaseRepository:
    """Supabase (PostgREST) repository. supabase-py is synchronous, so every call runs in a thread.

    Aggregations (stats, payment lookup) fetch the relevant rows and reuse the pure helpers above:
    fine at hackathon scale (hundreds of rows); move to SQL views/RPCs if the data grows.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, url: str, key: str) -> "SupabaseRepository":
        """Create a real supabase-py client."""
        from supabase import create_client

        return cls(create_client(url, key))

    async def _run(self, fn: Any) -> list[dict[str, Any]]:
        response = await asyncio.to_thread(fn)
        return list(response.data or [])

    def _table(self, name: str) -> Any:
        return self.client.table(name)

    # -- merchants --
    async def ping(self) -> str:
        """``ok`` if a trivial query succeeds."""
        await self._run(lambda: self._table("merchants").select("id").limit(1).execute())
        return "ok"

    def _merchant(self, row: dict[str, Any], handles: list[dict[str, Any]]) -> MerchantRecord:
        row = {**row, "logo_embedding": _parse_vector(row.get("logo_embedding"))}
        row["official_handles"] = [
            {"platform": h["platform"], "handle": h["handle"], "url": h.get("url")}
            for h in handles
            if h["merchant_id"] == row["id"]
        ]
        return MerchantRecord.model_validate(row)

    async def _merchants_where(self, column: str | None = None, value: Any = None) -> list[MerchantRecord]:
        def query() -> Any:
            q = self._table("merchants").select("*")
            return (q.eq(column, value) if column else q).execute()

        rows = await self._run(query)
        if not rows:
            return []
        ids = [r["id"] for r in rows]
        handles = await self._run(
            lambda: self._table("merchant_handles").select("*").in_("merchant_id", ids).execute()
        )
        return [self._merchant(r, handles) for r in rows]

    async def list_merchants(self) -> list[MerchantRecord]:
        """All merchants, oldest first."""
        return sorted(await self._merchants_where(), key=lambda m: (m.created_at, m.slug))

    async def get_merchant(self, merchant_id: UUID) -> MerchantRecord | None:
        """Merchant by id."""
        rows = await self._merchants_where("id", str(merchant_id))
        return rows[0] if rows else None

    async def get_merchant_by_slug(self, slug: str) -> MerchantRecord | None:
        """Merchant by slug."""
        rows = await self._merchants_where("slug", slug)
        return rows[0] if rows else None

    async def find_official_handle(self, platform: str, handle: str) -> MerchantRecord | None:
        """Exact official handle on the same platform."""
        p, h = _handle_key(platform, handle)
        rows = await self._run(
            lambda: (
                self._table("merchant_handles")
                .select("merchant_id")
                .eq("platform", p)
                .eq("handle", h)
                .execute()
            )
        )
        return await self.get_merchant(UUID(rows[0]["merchant_id"])) if rows else None

    async def find_by_payment(self, phone: str | None, till: str | None) -> PaymentLookup:
        """Facts about a phone or till."""
        number = canonical_number(phone) or canonical_number(till)
        if number is None:
            return PaymentLookup()
        merchants = await self.list_merchants()
        column = "reported_phone" if number.startswith("+") else "reported_till"
        reports = await self._run(
            lambda: self._table("community_reports").select("*").eq(column, number).execute()
        )
        array = "extracted_phones" if number.startswith("+") else "extracted_tills"
        threats = await self._run(
            lambda: self._table("threats").select("*").contains(array, [number]).execute()
        )
        return payment_lookup(
            number,
            merchants,
            [ReportRecord.model_validate(r) for r in reports],
            [self._threat(t) for t in threats],
        )

    async def create_merchant(
        self,
        data: MerchantCreate,
        hashes: LogoFeatures,
        *,
        logo_url: str | None = None,
        merchant_id: UUID | None = None,
        is_verified: bool = True,
        created_at: datetime | None = None,
    ) -> MerchantRecord:
        """Upsert a merchant and its handles (idempotent for the same id)."""
        record = build_merchant(
            data,
            hashes,
            logo_url=logo_url,
            merchant_id=merchant_id,
            is_verified=is_verified,
            created_at=created_at,
        )
        clash = await self.get_merchant_by_slug(record.slug)
        if clash and clash.id != record.id:
            raise Conflict("SLUG_TAKEN", f"Slug '{record.slug}' is already registered.")
        for h in record.official_handles:
            owner = await self.find_official_handle(h.platform, h.handle)
            if owner and owner.id != record.id:
                raise Conflict(
                    "HANDLE_TAKEN", "One of these handles is already registered to another merchant."
                )
        row = record.model_dump(mode="json", exclude={"official_handles"})
        row["logo_embedding"] = _vector(record.logo_embedding)
        await self._run(lambda: self._table("merchants").upsert(row, on_conflict="id").execute())
        handle_rows = [
            {
                "id": str(uuid.uuid5(record.id, f"{h.platform}:{h.handle}")),
                "merchant_id": str(record.id),
                "platform": h.platform,
                "handle": h.handle,
                "url": h.url,
            }
            for h in record.official_handles
        ]
        if handle_rows:
            await self._run(
                lambda: (
                    self._table("merchant_handles")
                    .upsert(handle_rows, on_conflict="platform,handle")
                    .execute()
                )
            )
        return record

    # -- threats --
    def _threat(self, row: dict[str, Any]) -> ThreatRecord:
        return ThreatRecord.model_validate(
            {**row, "avatar_embedding": _parse_vector(row.get("avatar_embedding"))}
        )

    def _threat_row(self, threat: ThreatRecord) -> dict[str, Any]:
        row = threat.model_dump(mode="json")
        row["avatar_embedding"] = _vector(threat.avatar_embedding)
        return row

    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord:
        """Insert or update on (merchant_id, platform, target_handle)."""
        existing = await self.get_threat_by_target(threat.merchant_id, threat.platform, threat.target_handle)
        record = merge_threat(existing, threat, utcnow())
        row = self._threat_row(record)
        await self._run(
            lambda: (
                self._table("threats").upsert(row, on_conflict="merchant_id,platform,target_handle").execute()
            )
        )
        return record

    async def get_threat_by_target(
        self, merchant_id: UUID, platform: str, handle: str
    ) -> ThreatRecord | None:
        """The threat for one page against one merchant."""
        p, h = _handle_key(platform, handle)
        rows = await self._run(
            lambda: (
                self._table("threats")
                .select("*")
                .eq("merchant_id", str(merchant_id))
                .eq("platform", p)
                .eq("target_handle", h)
                .execute()
            )
        )
        return self._threat(rows[0]) if rows else None

    async def list_threats(self, merchant_id: UUID, status: str | None) -> list[ThreatRecord]:
        """A merchant's threats, highest score first."""

        def query() -> Any:
            q = self._table("threats").select("*").eq("merchant_id", str(merchant_id))
            if status:
                q = q.eq("status", status)
            return q.order("composite_score", desc=True).execute()

        return [self._threat(r) for r in await self._run(query)]

    async def list_threats_by_status(self, statuses: Sequence[str]) -> list[ThreatRecord]:
        """Threats in any of ``statuses``."""
        rows = await self._run(
            lambda: self._table("threats").select("*").in_("status", list(statuses)).execute()
        )
        return [self._threat(r) for r in rows]

    async def get_threat(self, threat_id: UUID) -> ThreatRecord | None:
        """Threat by id."""
        rows = await self._run(lambda: self._table("threats").select("*").eq("id", str(threat_id)).execute())
        return self._threat(rows[0]) if rows else None

    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord:
        """Move a threat to ``status``. Raises NotFound."""
        threat = await self.get_threat(threat_id)
        if threat is None:
            raise NotFound(f"Threat {threat_id} not found.")
        updated = apply_status(threat, status, utcnow())
        patch = updated.model_dump(mode="json", include={"status", "status_history", "resolved_at"})
        await self._run(lambda: self._table("threats").update(patch).eq("id", str(threat_id)).execute())
        return updated

    # -- scans --
    async def insert_scan(self, scan: ScanCreate) -> UUID:
        """Store a scan (upsert on id, so seeding is idempotent)."""
        record = ScanRecord(
            **{**scan.model_dump(), "id": scan.id or uuid.uuid4(), "created_at": scan.created_at or utcnow()}
        )
        row = record.model_dump(mode="json")
        await self._run(lambda: self._table("scans").upsert(row, on_conflict="id").execute())
        return record.id

    async def get_scan(self, scan_id: UUID) -> ScanRecord | None:
        """Scan by id."""
        rows = await self._run(lambda: self._table("scans").select("*").eq("id", str(scan_id)).execute())
        return ScanRecord.model_validate(rows[0]) if rows else None

    async def latest_scan_for_threat(self, threat_id: UUID) -> ScanRecord | None:
        """Most recent scan linked to a threat."""
        rows = await self._run(
            lambda: (
                self._table("scans")
                .select("*")
                .eq("threat_id", str(threat_id))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        )
        return ScanRecord.model_validate(rows[0]) if rows else None

    # -- remediation --
    async def insert_remediation(self, log: RemediationCreate) -> None:
        """Append a remediation log row."""
        row = RemediationRecord(**log.model_dump(), id=uuid.uuid4(), created_at=utcnow()).model_dump(
            mode="json"
        )
        await self._run(lambda: self._table("remediation_logs").insert(row).execute())

    async def list_remediations(self, threat_id: UUID) -> list[RemediationRecord]:
        """A threat's generated playbooks, oldest first."""
        rows = await self._run(
            lambda: (
                self._table("remediation_logs")
                .select("*")
                .eq("threat_id", str(threat_id))
                .order("created_at")
                .execute()
            )
        )
        return [RemediationRecord.model_validate(r) for r in rows]

    # -- reports --
    async def insert_report(
        self,
        report: ReportCreate,
        *,
        report_id: UUID | None = None,
        status: str = "pending",
        threat_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> UUID:
        """Store a community report (upsert on id)."""
        record = _report_record(report, report_id, status, threat_id, created_at)
        row = record.model_dump(mode="json")
        await self._run(lambda: self._table("community_reports").upsert(row, on_conflict="id").execute())
        return record.id

    async def set_report_status(self, report_id: UUID, status: str) -> None:
        """Confirm or reject a report. Raises NotFound."""
        rows = await self._run(
            lambda: (
                self._table("community_reports").update({"status": status}).eq("id", str(report_id)).execute()
            )
        )
        if not rows:
            raise NotFound(f"Report {report_id} not found.")

    async def confirmed_reported_numbers(self) -> frozenset[str]:
        """Canonical phones/tills from confirmed reports."""
        rows = await self._run(
            lambda: self._table("community_reports").select("*").eq("status", "confirmed").execute()
        )
        return _confirmed_numbers(ReportRecord.model_validate(r) for r in rows)

    # -- alerts --
    async def insert_alert(self, alert: AlertCreate) -> AlertRecord:
        """Store an alert (upsert on id)."""
        record = AlertRecord(
            **{
                **alert.model_dump(),
                "id": alert.id or uuid.uuid4(),
                "created_at": alert.created_at or utcnow(),
            }
        )
        row = record.model_dump(mode="json")
        await self._run(lambda: self._table("merchant_alerts").upsert(row, on_conflict="id").execute())
        return record

    async def last_alert_for_threat(self, threat_id: UUID) -> AlertRecord | None:
        """Most recent alert for a threat."""
        rows = await self._run(
            lambda: (
                self._table("merchant_alerts")
                .select("*")
                .eq("threat_id", str(threat_id))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        )
        return AlertRecord.model_validate(rows[0]) if rows else None

    async def list_alerts(
        self, merchant_id: UUID, since: datetime | None, unread_only: bool, limit: int
    ) -> list[AlertRecord]:
        """Alerts newer than ``since`` (exclusive), newest first."""

        def query() -> Any:
            q = self._table("merchant_alerts").select("*").eq("merchant_id", str(merchant_id))
            if since is not None:
                q = q.gt("created_at", _iso(since))
            if unread_only:
                q = q.is_("read_at", "null")
            return q.order("created_at", desc=True).limit(limit).execute()

        return [AlertRecord.model_validate(r) for r in await self._run(query)]

    async def unread_count(self, merchant_id: UUID) -> int:
        """Number of unread alerts."""
        rows = await self._run(
            lambda: (
                self._table("merchant_alerts")
                .select("id")
                .eq("merchant_id", str(merchant_id))
                .is_("read_at", "null")
                .execute()
            )
        )
        return len(rows)

    async def mark_alerts_read(self, merchant_id: UUID, ids: list[UUID] | None) -> int:
        """Mark ``ids`` (or all when None) read; returns the remaining unread count."""
        patch = {"read_at": _iso(utcnow())}

        def query() -> Any:
            q = (
                self._table("merchant_alerts")
                .update(patch)
                .eq("merchant_id", str(merchant_id))
                .is_("read_at", "null")
            )
            if ids is not None:
                q = q.in_("id", [str(i) for i in ids])
            return q.execute()

        if ids is None or ids:
            await self._run(query)
        return await self.unread_count(merchant_id)

    # -- target profiles --
    async def get_target_profile(self, platform: str, handle: str) -> TargetProfileRecord | None:
        """Tier-1 known page."""
        p, h = _handle_key(platform, handle)
        rows = await self._run(
            lambda: self._table("target_profiles").select("*").eq("platform", p).eq("handle", h).execute()
        )
        if not rows:
            return None
        return TargetProfileRecord.model_validate(
            {**rows[0], "avatar_embedding": _parse_vector(rows[0].get("avatar_embedding"))}
        )

    async def upsert_target_profile(self, profile: TargetProfileRecord) -> None:
        """Store a seeded or OpenGraph-fetched page profile."""
        row = profile.model_dump(mode="json")
        row["avatar_embedding"] = _vector(profile.avatar_embedding)
        await self._run(
            lambda: self._table("target_profiles").upsert(row, on_conflict="platform,handle").execute()
        )

    # -- stats --
    async def stats(self, merchant_id: UUID | None) -> Stats:
        """KPIs over stored rows."""
        merchants = await self.list_merchants()
        threats = [
            self._threat(r) for r in await self._run(lambda: self._table("threats").select("*").execute())
        ]
        scan_rows = await self._run(
            lambda: (
                self._table("scans")
                .select("id,merchant_id,verdict,source,elapsed_ms,created_at,input_value,input_kind,result")
                .execute()
            )
        )
        scans = [ScanRecord.model_validate(r) for r in scan_rows]
        return compute_stats(merchants, threats, scans, merchant_id, utcnow())

    # -- seeding --
    async def delete_rows(self, table: str, column: str, values: Sequence[str]) -> None:
        """Delete rows whose ``column`` is in ``values`` (used by ``mock_seeder --reset``)."""
        if values:
            await self._run(lambda: self._table(table).delete().in_(column, list(values)).execute())
