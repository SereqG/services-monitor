from __future__ import annotations

import re

from pydantic import BaseModel, field_validator


class AuditInput(BaseModel):
    url: str
    report_name: str | None = None

    @field_validator("url")
    @classmethod
    def url_must_be_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("URL must use HTTPS")
        return v

    @field_validator("report_name")
    @classmethod
    def sanitize_report_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        sanitized = re.sub(r"[^\w\s\-]", "", v).strip()
        return sanitized[:200] if sanitized else None


class ValidationResult(BaseModel):
    url: str
    report_name: str | None
    is_valid: bool
    errors: list[str]
