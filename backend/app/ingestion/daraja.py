"""Safaricom Daraja API integration for live M-Pesa till/paybill owner validation (TSK-039).

Spec: docs/BACKEND.md section 6.5 & future_spec.md section 3.1.

Capabilities:
1. OAuth 2.0 token generation (/oauth/v1/generate?grant_type=client_credentials).
2. Live M-Pesa account/business name query & KYC validation (/mpesa/accountname/v1/query).
3. Resilient fallback to a deterministic simulated resolver when credentials are absent,
   when running in DEMO_MODE, or upon network failure without leaking errors.
"""

import asyncio
import hashlib
import logging
import time
from typing import Any, Literal

import httpx

from app.core.config import Settings, get_settings
from app.engine.payment import canonical_phone, canonical_till
from app.schemas.report import DarajaValidation

log = logging.getLogger("halisi.daraja")


class DarajaError(Exception):
    """Base exception for Safaricom Daraja API errors."""


class DarajaAuthError(DarajaError):
    """Authentication or OAuth token failure."""


class DarajaRequestError(DarajaError):
    """Network or API request failure during account lookup."""


class DarajaAccountNotFoundError(DarajaError):
    """Queried phone number, till, or paybill does not exist on M-Pesa."""


KENYAN_FIRST_NAMES: tuple[str, ...] = (
    "JAMES",
    "JOHN",
    "PETER",
    "MARY",
    "GRACE",
    "ESTHER",
    "BRIAN",
    "KEVIN",
    "MERCY",
    "FAITH",
    "DANIEL",
    "SARAH",
    "JOSEPH",
    "BEATRICE",
    "GEOFFREY",
    "COLLINS",
    "DENNIS",
)

KENYAN_SURNAMES: tuple[str, ...] = (
    "KIPROP",
    "MWANGI",
    "OTIENO",
    "WANJIKU",
    "KIMANI",
    "ODHIAMBO",
    "MUTUA",
    "KORIR",
    "CHERUIYOT",
    "MAINA",
    "KAMAU",
    "NJOROGE",
    "OCHIENG",
    "BARASA",
    "WANYONYI",
)


def _deterministic_name(seed_str: str) -> str:
    """Generate a realistic, deterministic Kenyan name from a phone number seed."""
    h = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
    fn = KENYAN_FIRST_NAMES[h % len(KENYAN_FIRST_NAMES)]
    sn = KENYAN_SURNAMES[(h // len(KENYAN_FIRST_NAMES)) % len(KENYAN_SURNAMES)]
    return f"{fn} {sn}"


SIMULATED_ACCOUNTS: dict[str, dict[str, Any]] = {
    # Official Halisi merchants
    "543210": {
        "name": "NAIROBI SNEAKER VAULT",
        "type": "till",
        "kyc": "verified",
        "is_valid": True,
    },
    "400200": {
        "name": "KILIMANI GLOW",
        "type": "paybill",
        "kyc": "verified",
        "is_valid": True,
    },
    "778899": {
        "name": "M-CHAZI ELECTRONICS",
        "type": "till",
        "kyc": "verified",
        "is_valid": True,
    },
    "+254700111222": {
        "name": "COLLINS KIMANZI",
        "type": "phone",
        "kyc": "verified",
        "is_valid": True,
    },
    "+254711223344": {
        "name": "FAITH MUTUA",
        "type": "phone",
        "kyc": "verified",
        "is_valid": True,
    },
    "+254722334455": {
        "name": "GEOFFREY OBWOCHA",
        "type": "phone",
        "kyc": "verified",
        "is_valid": True,
    },
    # Competitor till (legit competitor, not registered with Halisi)
    "889900": {
        "name": "KICKS KENYA LIMITED",
        "type": "till",
        "kyc": "verified",
        "is_valid": True,
    },
    # Known reported scam lines / clone targets
    "+254798999111": {
        "name": "JOHN KAMAU NJOROGE",
        "type": "phone",
        "kyc": "active",
        "is_valid": True,
    },
    "+254798555444": {
        "name": "DENNIS OCHIENG",
        "type": "phone",
        "kyc": "active",
        "is_valid": True,
    },
    "+254712999888": {
        "name": "MARY WANJIKU",
        "type": "phone",
        "kyc": "active",
        "is_valid": True,
    },
}


class DarajaClient:
    """Safaricom Daraja API client with token caching and simulated fallback."""

    def __init__(
        self,
        settings: Settings | None = None,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._http = http
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def base_url(self) -> str:
        """Configured Daraja API base URL."""
        return self.settings.daraja_api_base_url

    @property
    def is_live(self) -> bool:
        """Whether live requests should be attempted."""
        return self.settings.daraja_live_available

    @staticmethod
    def _normalize_identifier(
        number: str,
        kind: Literal["phone", "till", "paybill"] | None = None,
    ) -> tuple[str | None, Literal["phone", "till", "paybill"] | None]:
        """Normalize Kenyan mobile phone or till string."""
        clean = (number or "").strip()
        phone = canonical_phone(clean)
        if phone:
            return phone, "phone"
        till = canonical_till(clean)
        if till:
            determined = kind if kind in ("till", "paybill") else ("till" if len(till) <= 6 else "paybill")
            return till, determined
        return None, None

    async def get_access_token(self, http: httpx.AsyncClient | None = None) -> str:
        """Obtain a valid OAuth 2.0 Bearer token, renewing when expired."""
        if not self.is_live:
            return "simulated_daraja_access_token"

        now = time.monotonic()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        async with self._lock:
            now = time.monotonic()
            if self._token and now < self._token_expires_at - 60:
                return self._token

            client = http or self._http
            should_close = False
            if client is None:
                client = httpx.AsyncClient(timeout=self.settings.daraja_timeout_seconds)
                should_close = True

            try:
                url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
                auth = (self.settings.daraja_consumer_key, self.settings.daraja_consumer_secret)
                resp = await client.get(url, auth=auth)
                if resp.status_code != 200:
                    raise DarajaAuthError(
                        f"Daraja OAuth failed with HTTP {resp.status_code}: {resp.text}"
                    )
                data = resp.json()
                token = data.get("access_token")
                if not token:
                    raise DarajaAuthError("No access_token returned in Daraja OAuth response.")
                expires_in = int(data.get("expires_in", 3599))
                self._token = token
                self._token_expires_at = time.monotonic() + expires_in
                return token
            finally:
                if should_close:
                    await client.aclose()

    async def validate_account(
        self,
        number: str,
        kind: Literal["phone", "till", "paybill"] | None = None,
        http: httpx.AsyncClient | None = None,
    ) -> DarajaValidation:
        """Validate phone/till/paybill identity via live Daraja or simulated resolver."""
        normalized, determined_kind = self._normalize_identifier(number, kind)
        if normalized is None:
            return DarajaValidation(
                is_valid=False,
                account_name=None,
                account_type="unknown",
                kyc_status="not_found",
                source="fallback",
                error_message="Invalid Kenyan mobile phone or till number format",
                operator="Safaricom M-Pesa",
            )

        if not self.is_live:
            return self.mock_validate(normalized, kind=determined_kind)

        client = http or self._http
        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.settings.daraja_timeout_seconds)
            should_close = True

        try:
            token = await self.get_access_token(http=client)
            url = f"{self.base_url}/mpesa/accountname/v1/query"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            ident_type = "1" if determined_kind == "phone" else ("2" if determined_kind == "till" else "4")
            payload = {
                "Initiator": self.settings.daraja_initiator_name,
                "SecurityCredential": self.settings.daraja_security_credential,
                "CommandID": "AccountNameInquiry",
                "PartyA": self.settings.daraja_shortcode,
                "PartyB": normalized.lstrip("+"),
                "IdentifierType": ident_type,
                "Remarks": "Halisi Account Validation",
                "QueueTimeOutURL": "https://halisi.africa/api/v1/daraja/timeout",
                "ResultURL": "https://halisi.africa/api/v1/daraja/result",
            }
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                resp_code = str(data.get("ResponseCode", "0"))
                if resp_code == "0":
                    account_name = (
                        data.get("AccountName")
                        or data.get("BusinessName")
                        or data.get("ResultDesc")
                    )
                    kyc = str(data.get("KYCStatus", "verified")).lower()
                    return DarajaValidation(
                        is_valid=True,
                        account_name=account_name,
                        account_type=determined_kind or "unknown",
                        kyc_status=kyc if kyc in ("verified", "active", "dormant") else "active",
                        source="live",
                        operator="Safaricom M-Pesa",
                    )
                msg = data.get("ResponseDescription") or data.get("errorMessage") or "Account query rejected"
                return DarajaValidation(
                    is_valid=False,
                    account_name=None,
                    account_type=determined_kind or "unknown",
                    kyc_status="not_found",
                    source="live",
                    error_message=msg,
                    operator="Safaricom M-Pesa",
                )
            if resp.status_code == 404:
                return DarajaValidation(
                    is_valid=False,
                    account_name=None,
                    account_type=determined_kind or "unknown",
                    kyc_status="not_found",
                    source="live",
                    error_message="Identifier not registered on M-Pesa",
                    operator="Safaricom M-Pesa",
                )
            raise DarajaRequestError(f"HTTP {resp.status_code}: {resp.text}")
        except Exception as exc:
            log.warning("Daraja live API error: %s; falling back to simulated resolver", exc)
            sim = self.mock_validate(normalized, kind=determined_kind)
            return DarajaValidation(
                is_valid=sim.is_valid,
                account_name=sim.account_name,
                account_type=sim.account_type,
                kyc_status=sim.kyc_status,
                source="fallback",
                error_message=f"Live API error: {exc}",
                operator="Safaricom M-Pesa",
            )
        finally:
            if should_close:
                await client.aclose()

    def mock_validate(
        self,
        number: str,
        kind: Literal["phone", "till", "paybill"] | None = None,
    ) -> DarajaValidation:
        """Deterministic mock/sandbox resolver without network calls."""
        normalized, determined_kind = self._normalize_identifier(number, kind)
        if normalized is None:
            return DarajaValidation(
                is_valid=False,
                account_name=None,
                account_type="unknown",
                kyc_status="not_found",
                source="simulated",
                error_message="Invalid Kenyan mobile phone or till number format",
                operator="Safaricom M-Pesa",
            )

        if normalized in SIMULATED_ACCOUNTS:
            acc = SIMULATED_ACCOUNTS[normalized]
            return DarajaValidation(
                is_valid=acc["is_valid"],
                account_name=acc["name"],
                account_type=acc["type"],
                kyc_status=acc["kyc"],
                source="simulated",
                operator="Safaricom M-Pesa",
            )

        if determined_kind == "phone":
            account_name = _deterministic_name(normalized)
            return DarajaValidation(
                is_valid=True,
                account_name=account_name,
                account_type="phone",
                kyc_status="active",
                source="simulated",
                operator="Safaricom M-Pesa",
            )

        acc_type = determined_kind or ("till" if len(normalized) <= 6 else "paybill")
        return DarajaValidation(
            is_valid=True,
            account_name=f"ENTERPRISE {normalized}",
            account_type=acc_type,
            kyc_status="active",
            source="simulated",
            operator="Safaricom M-Pesa",
        )
