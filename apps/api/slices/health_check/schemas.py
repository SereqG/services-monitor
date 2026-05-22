from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class HttpStatus(str, Enum):
    ok = "ok"
    redirect = "redirect"
    client_error = "client_error"
    server_error = "server_error"
    timeout = "timeout"
    connection_error = "connection_error"


class RedirectHop(BaseModel):
    url: str
    status_code: int


class HealthCheckResult(BaseModel):
    url: str
    final_url: str
    status_code: int | None
    status: HttpStatus
    ttfb_ms: float | None
    redirect_chain: list[RedirectHop]
    has_redirect_loop: bool
    is_available: bool
    error: str | None = None
