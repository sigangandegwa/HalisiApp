from typing import Protocol, List, Optional
from datetime import datetime
from uuid import UUID
import asyncio
from supabase import create_client, Client
from app.schemas.merchant import MerchantRecord, MerchantCreate, LogoFeatures, PaymentLookup
from app.schemas.threat import ThreatRecord, ThreatUpsert
from app.schemas.check import ScanRecord, ScanCreate
from app.schemas.remediation import RemediationCreate
from app.schemas.report import ReportCreate
from app.schemas.report import Stats
from app.schemas.alert import AlertCreate, AlertRecord
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
    async def find_threat_by_target(self, platform: str, target_handle: str) -> Optional[ThreatRecord]: ...
    async def update_threat_status(self, threat_id: UUID, status: str) -> ThreatRecord: ...
    async def insert_scan(self, scan: ScanCreate) -> UUID: ...
    async def get_scan(self, scan_id: UUID) -> Optional[ScanRecord]: ...
    async def insert_remediation(self, log: RemediationCreate) -> None: ...
    async def insert_report(self, report: ReportCreate) -> UUID: ...
    async def stats(self, merchant_id: Optional[UUID]) -> Stats: ...
    async def insert_alert(self, alert: AlertCreate) -> AlertRecord: ...
    async def last_alert_for_threat(self, threat_id: UUID) -> Optional[AlertRecord]: ...
    async def list_alerts(self, merchant_id: UUID, since: Optional[datetime], unread_only: bool, limit: int) -> List[AlertRecord]: ...
    async def mark_alerts_read(self, merchant_id: UUID, ids: Optional[List[UUID]]) -> int: ...

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
        kind = "phone" if phone else "till"
        val = phone or till
        from app.engine.payment import mask_phone
        display = mask_phone(val) if kind == "phone" else val
        
        merchant = None
        status = "unknown"
        
        merchants_resp = await asyncio.to_thread(self.client.table("merchants").select("*").execute)
        for m in merchants_resp.data:
            if phone and phone in m.get("phone_numbers", []):
                merchant = m
                status = "official"
                break
            if till and till == m.get("mpesa_number") and m.get("mpesa_type") in ["till", "paybill"]:
                merchant = m
                status = "official"
                break
            if phone and phone == m.get("mpesa_number") and m.get("mpesa_type") == "pochi":
                merchant = m
                status = "official"
                break
                
        report_count = 0
        linked_threats = 0
        if status != "official":
            if phone:
                reports_resp = await asyncio.to_thread(self.client.table("community_reports").select("*").eq("reported_phone", phone).execute)
            else:
                reports_resp = await asyncio.to_thread(self.client.table("community_reports").select("*").eq("reported_till", till).execute)
            
            reports = reports_resp.data
            report_count = len(reports)
            confirmed = any(r.get("status") == "confirmed" for r in reports)
            if confirmed:
                status = "reported"
            linked_threats = len(set(r.get("threat_id") for r in reports if r.get("threat_id")))
            
        merchant_record = MerchantRecord(**merchant) if merchant else None
        
        return PaymentLookup(
            kind=kind,
            normalized=val,
            display=display,
            status=status,
            merchant=merchant_record,
            report_count=report_count,
            linked_threats=linked_threats
        )

    async def create_merchant(self, data: MerchantCreate, hashes: LogoFeatures) -> MerchantRecord:
        raise NotImplementedError

    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord:
        raise NotImplementedError

    async def list_threats(self, merchant_id: UUID, status: Optional[str]) -> List[ThreatRecord]:
        return []

    async def get_threat(self, threat_id: UUID) -> Optional[ThreatRecord]:
        return None

    async def find_threat_by_target(self, platform: str, target_handle: str) -> Optional[ThreatRecord]:
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
        data = report.model_dump(exclude_none=True)
        resp = await asyncio.to_thread(self.client.table("community_reports").insert(data).execute)
        return UUID(resp.data[0]["id"])

    async def stats(self, merchant_id: Optional[UUID]) -> Stats:
        return Stats(pages_scanned=0, threats_detected=0, impersonations_blocked_7d=0, merchants_protected=0, median_detection_ms=0, top_platforms=[])

    async def insert_alert(self, alert: AlertCreate) -> AlertRecord:
        raise NotImplementedError

    async def last_alert_for_threat(self, threat_id: UUID) -> Optional[AlertRecord]:
        return None

    async def list_alerts(self, merchant_id: UUID, since: Optional[datetime], unread_only: bool, limit: int) -> List[AlertRecord]:
        return []

    async def mark_alerts_read(self, merchant_id: UUID, ids: Optional[List[UUID]]) -> int:
        return 0

class MemoryRepository(Repository):
    def __init__(self):
        from uuid import uuid4
        import json
        from pathlib import Path
        self.alerts = []
        self.merchants = []
        self.reports = []
        base_dir = Path(__file__).resolve().parent.parent
        fixtures_dir = base_dir / "ingestion" / "fixtures"
        if (fixtures_dir / "merchants.json").exists():
            with open(fixtures_dir / "merchants.json") as f:
                self.merchants = json.load(f)
        if (fixtures_dir / "reports.json").exists():
            with open(fixtures_dir / "reports.json") as f:
                self.reports = json.load(f)

    async def list_merchants(self) -> List[MerchantRecord]:
        return []

    async def get_merchant(self, merchant_id: UUID) -> Optional[MerchantRecord]:
        return None

    async def get_merchant_by_slug(self, slug: str) -> Optional[MerchantRecord]:
        return None

    async def find_official_handle(self, platform: str, handle: str) -> Optional[MerchantRecord]:
        return None

    async def find_by_payment(self, phone: Optional[str], till: Optional[str]) -> PaymentLookup:
        kind = "phone" if phone else "till"
        val = phone or till
        from app.engine.payment import mask_phone
        display = mask_phone(val) if kind == "phone" else val
        
        merchant = None
        status = "unknown"
        
        for m in self.merchants:
            if phone and phone in m.get("phone_numbers", []):
                merchant = m
                status = "official"
                break
            if till and till == m.get("mpesa_number") and m.get("mpesa_type") in ["till", "paybill"]:
                merchant = m
                status = "official"
                break
            if phone and phone == m.get("mpesa_number") and m.get("mpesa_type") == "pochi":
                merchant = m
                status = "official"
                break
                
        report_count = 0
        linked_threats = 0
        if status != "official":
            if phone:
                reports = [r for r in self.reports if r.get("reported_phone") == phone]
            else:
                reports = [r for r in self.reports if r.get("reported_till") == till]
            report_count = len(reports)
            if any(r.get("status") == "confirmed" for r in reports):
                status = "reported"
            linked_threats = len(set(r.get("threat_id") for r in reports if r.get("threat_id")))
            
        merchant_record = MerchantRecord(**merchant) if merchant else None
        return PaymentLookup(
            kind=kind,
            normalized=val,
            display=display,
            status=status,
            merchant=merchant_record,
            report_count=report_count,
            linked_threats=linked_threats
        )

    async def create_merchant(self, data: MerchantCreate, hashes: LogoFeatures) -> MerchantRecord:
        raise NotImplementedError

    async def upsert_threat(self, threat: ThreatUpsert) -> ThreatRecord:
        raise NotImplementedError

    async def list_threats(self, merchant_id: UUID, status: Optional[str]) -> List[ThreatRecord]:
        return []

    async def get_threat(self, threat_id: UUID) -> Optional[ThreatRecord]:
        return None

    async def find_threat_by_target(self, platform: str, target_handle: str) -> Optional[ThreatRecord]:
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
        from uuid import uuid4
        report_id = uuid4()
        data = report.model_dump(exclude_none=True)
        data["id"] = str(report_id)
        data["status"] = "pending"
        data["created_at"] = datetime.utcnow().isoformat()
        self.reports.append(data)
        return report_id

    async def stats(self, merchant_id: Optional[UUID]) -> Stats:
        return Stats(pages_scanned=0, threats_detected=0, impersonations_blocked_7d=0, merchants_protected=0, median_detection_ms=0, top_platforms=[])

    async def insert_alert(self, alert: AlertCreate) -> AlertRecord:
        from uuid import uuid4
        record = AlertRecord(**alert.model_dump(), id=uuid4(), created_at=datetime.utcnow())
        self.alerts.append(record)
        return record

    async def last_alert_for_threat(self, threat_id: UUID) -> Optional[AlertRecord]:
        matching = [a for a in self.alerts if a.threat_id == threat_id]
        if not matching:
            return None
        return sorted(matching, key=lambda x: x.created_at, reverse=True)[0]

    async def list_alerts(self, merchant_id: UUID, since: Optional[datetime], unread_only: bool, limit: int) -> List[AlertRecord]:
        filtered = [a for a in self.alerts if a.merchant_id == merchant_id]
        if unread_only:
            filtered = [a for a in filtered if a.read_at is None]
        if since:
            filtered = [a for a in filtered if a.created_at > since]
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[:limit]

    async def mark_alerts_read(self, merchant_id: UUID, ids: Optional[List[UUID]]) -> int:
        count = 0
        now = datetime.utcnow()
        for alert in self.alerts:
            if alert.merchant_id == merchant_id and alert.read_at is None:
                if ids is None or alert.id in ids:
                    alert.read_at = now
                    count += 1
        return count
