from typing import Protocol, List, Optional
from uuid import UUID
import asyncio
from supabase import create_client, Client
from app.schemas.merchant import MerchantRecord, MerchantCreate, LogoFeatures, PaymentLookup
from app.schemas.threat import ThreatRecord, ThreatUpsert
from app.schemas.check import ScanRecord, ScanCreate
from app.schemas.remediation import RemediationCreate
from app.schemas.report import ReportCreate
from app.schemas.report import Stats
from app.core.config import settings

class Repository(Protocol):
    async def list_merchants(self) -> List[MerchantRecord]: ...
    async def get_merchant(self, merchant_id: UUID) -> Optional[MerchantRecord]: ...
    async def get_merchant_by_slug(self, slug: str) -> Optional[MerchantRecord]: ...
    async def find_official_handle(self, platform: str, handle: str) -> Optional[MerchantRecord]: ...
    async def find_by_payment(self, phone: Optional[str], till: Optional[str]) -> PaymentLookup: ...
    async def create_merchant(self, data: MerchantCreate, hashes: LogoFeatures) -> MerchantRecord: ...
    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord: ...
    async def list_threats(self, merchant_id: UUID, status: Optional[str]) -> List[ThreatRecord]: ...
    async def get_threat(self, threat_id: UUID) -> Optional[ThreatRecord]: ...
    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord: ...
    async def insert_scan(self, scan: ScanCreate) -> UUID: ...
    async def get_scan(self, scan_id: UUID) -> Optional[ScanRecord]: ...
    async def insert_remediation(self, log: RemediationCreate) -> None: ...
    async def insert_report(self, report: ReportCreate) -> UUID: ...
    async def stats(self, merchant_id: Optional[UUID]) -> Stats: ...

class SupabaseRepository(Repository):
    def __init__(self):
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    async def list_merchants(self) -> List[MerchantRecord]:
        return []

    async def get_merchant(self, merchant_id: UUID) -> Optional[MerchantRecord]:
        return None

    async def get_merchant_by_slug(self, slug: str) -> Optional[MerchantRecord]:
        return None

    async def find_official_handle(self, platform: str, handle: str) -> Optional[MerchantRecord]:
        return None

    async def find_by_payment(self, phone: Optional[str], till: Optional[str]) -> PaymentLookup:
        return PaymentLookup(kind="unknown", normalized="", display="", status="unknown", report_count=0, linked_threats=0)

    async def create_merchant(self, data: MerchantCreate, hashes: LogoFeatures) -> MerchantRecord:
        raise NotImplementedError

    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord:
        raise NotImplementedError

    async def list_threats(self, merchant_id: UUID, status: Optional[str]) -> List[ThreatRecord]:
        return []

    async def get_threat(self, threat_id: UUID) -> Optional[ThreatRecord]:
        return None

    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord:
        raise NotImplementedError

    async def insert_scan(self, scan: ScanCreate) -> UUID:
        raise NotImplementedError

    async def get_scan(self, scan_id: UUID) -> Optional[ScanRecord]:
        return None

    async def insert_remediation(self, log: RemediationCreate) -> None:
        pass

    async def insert_report(self, report: ReportCreate) -> UUID:
        raise NotImplementedError

    async def stats(self, merchant_id: Optional[UUID]) -> Stats:
        return Stats(pages_scanned=0, threats_detected=0, impersonations_blocked_7d=0, merchants_protected=0, median_detection_ms=0, top_platforms=[])

class MemoryRepository(Repository):
    # In-memory implementation for DEMO_MODE
    async def list_merchants(self) -> List[MerchantRecord]:
        return []

    async def get_merchant(self, merchant_id: UUID) -> Optional[MerchantRecord]:
        return None

    async def get_merchant_by_slug(self, slug: str) -> Optional[MerchantRecord]:
        return None

    async def find_official_handle(self, platform: str, handle: str) -> Optional[MerchantRecord]:
        return None

    async def find_by_payment(self, phone: Optional[str], till: Optional[str]) -> PaymentLookup:
        return PaymentLookup(kind="unknown", normalized="", display="", status="unknown", report_count=0, linked_threats=0)

    async def create_merchant(self, data: MerchantCreate, hashes: LogoFeatures) -> MerchantRecord:
        raise NotImplementedError

    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord:
        raise NotImplementedError

    async def list_threats(self, merchant_id: UUID, status: Optional[str]) -> List[ThreatRecord]:
        return []

    async def get_threat(self, threat_id: UUID) -> Optional[ThreatRecord]:
        return None

    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord:
        raise NotImplementedError

    async def insert_scan(self, scan: ScanCreate) -> UUID:
        raise NotImplementedError

    async def get_scan(self, scan_id: UUID) -> Optional[ScanRecord]:
        return None

    async def insert_remediation(self, log: RemediationCreate) -> None:
        pass

    async def insert_report(self, report: ReportCreate) -> UUID:
        raise NotImplementedError

    async def stats(self, merchant_id: Optional[UUID]) -> Stats:
        return Stats(pages_scanned=0, threats_detected=0, impersonations_blocked_7d=0, merchants_protected=0, median_detection_ms=0, top_platforms=[])
