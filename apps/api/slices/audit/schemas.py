from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

from core.config import settings
from slices.discovery.schemas import DiscoveryResult
from slices.reporting.schemas import AuditReport

AuditCheckType = Literal["health", "seo", "accessibility", "security"]

ALL_CHECKS: tuple[AuditCheckType, ...] = ("health", "seo", "accessibility", "security")


class AuditRequest(BaseModel):
    url: str
    email: EmailStr
    report_name: str | None = None
    selected_urls: list[str] | None = None
    discovery_result: DiscoveryResult | None = None
    scope: list[AuditCheckType] | None = None
    max_sites: int | None = None
    max_depth: int | None = None
    enable_ai_summary: bool = False

    @field_validator("max_sites")
    @classmethod
    def cap_max_sites(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 1:
            raise ValueError("max_sites must be at least 1")
        return min(v, settings.discovery_max_urls)

    @field_validator("max_depth")
    @classmethod
    def cap_max_depth(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 0:
            raise ValueError("max_depth must be 0 or greater")
        return min(v, settings.discovery_max_depth)


class AuditResponse(BaseModel):
    success: bool
    report: AuditReport


class AuditEventType(str, Enum):
    phase = "phase"
    complete = "complete"


class AuditEvent(BaseModel):
    type: AuditEventType
    message: str
    elapsed_seconds: float | None = None
    max_duration_seconds: int | None = None
    result: AuditReport | None = None
