"""Domain exceptions and their JSON mapping: ``{"error": {"code": "...", "message": "..."}}``.

Handlers never leak stack traces or internal details; details are only logged.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("halisi.errors")


class HalisiError(Exception):
    """Base domain error with an HTTP status and a stable machine-readable code."""

    status_code = 400
    code = "BAD_REQUEST"
    message = "Bad request."

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        if code:
            self.code = code


class InvalidInput(HalisiError):
    """422: well-formed JSON but unusable input."""

    status_code, code, message = 422, "INVALID_INPUT", "The input is not valid."


class UnsupportedPlatform(HalisiError):
    """422: not a supported profile link / handle."""

    status_code, code, message = 422, "UNSUPPORTED_PLATFORM", "This link or handle is not supported."


class PaymentInput(HalisiError):
    """422: a phone/till was sent to ``/check``; the client should call ``/verify/payment``."""

    status_code, code, message = 422, "PAYMENT_INPUT", "This is a phone or till number: use /verify/payment."


class InvalidImage(HalisiError):
    """422: the uploaded / fetched image can't be used."""

    status_code, code, message = 422, "INVALID_IMAGE", "The image could not be read."


class NotFoundError(HalisiError):
    """404."""

    status_code, code, message = 404, "NOT_FOUND", "Not found."


class ConflictError(HalisiError):
    """409."""

    status_code, code, message = 409, "CONFLICT", "Conflict."


class Unauthorized(HalisiError):
    """401: missing or wrong ``X-Halisi-Key``."""

    status_code, code, message = 401, "UNAUTHORIZED", "A valid API key is required."


class RateLimited(HalisiError):
    """429."""

    status_code, code, message = 429, "RATE_LIMITED", "Too many requests. Please wait a minute and try again."


class TargetUnreachable(HalisiError):
    """502: the page couldn't be fetched; the frontend offers the manual fallback."""

    status_code, code, message = (
        502,
        "TARGET_UNREACHABLE",
        "We couldn't open that page. Paste its details instead.",
    )


def _body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


def install_error_handlers(app: FastAPI) -> None:
    """Register JSON error handlers on ``app``."""

    @app.exception_handler(HalisiError)
    async def _domain(_: Request, exc: HalisiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", ()) if p != "body")
        message = (
            f"{where}: {first.get('msg', 'invalid')}" if where else str(first.get("msg", "Invalid input."))
        )
        return JSONResponse(status_code=422, content=_body("INVALID_INPUT", message[:300]))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 413: "PAYLOAD_TOO_LARGE"}
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code, content=_body(codes.get(exc.status_code, "HTTP_ERROR"), message)
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled error on %s %s: %r", request.method, request.url.path, exc, exc_info=exc)
        return JSONResponse(status_code=500, content=_body("INTERNAL_ERROR", "An unexpected error occurred."))
