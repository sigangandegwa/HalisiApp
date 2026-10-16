"""Authentication schemas for merchant dashboard login and session management."""

from pydantic import Field

from app.schemas.common import BaseSchema


class LoginRequest(BaseSchema):
    """POST /auth/login request body."""

    identifier: str | None = Field(default=None, description="Merchant slug, business name, or official handle")
    passcode: str = Field(..., description="Merchant dashboard passcode")


class LoginResponse(BaseSchema):
    """POST /auth/login response."""

    ok: bool = True
    merchant_id: str
    merchant_slug: str
    business_name: str


class LogoutResponse(BaseSchema):
    """POST /auth/logout response."""

    ok: bool = True
    message: str = "Logged out successfully"
