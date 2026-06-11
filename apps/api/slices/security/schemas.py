from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    informational = "informational"


class SecurityFinding(BaseModel):
    code: str  # stable identifier; the deterministic key clients localize by
    category: str
    title: str  # English; deterministic source of truth
    description: str
    severity: Severity
    # Structured values behind any interpolated title/description (e.g. the
    # header or cookie name), so clients can render a localized template.
    params: dict[str, str | int] = {}
    evidence: str | None = None
    affected_resource: str | None = None
    remediation: str | None = None


class HeadersResult(BaseModel):
    score: int
    headers_present: list[str]
    headers_missing: list[str]
    findings: list[SecurityFinding]


class TlsResult(BaseModel):
    score: int
    tls_version: str | None
    certificate_valid: bool | None
    certificate_expiry_days: int | None
    findings: list[SecurityFinding]


class CookieResult(BaseModel):
    score: int
    total_cookies: int
    findings: list[SecurityFinding]


class DnsResult(BaseModel):
    score: int
    spf_present: bool
    dmarc_present: bool
    dnssec_enabled: bool
    caa_present: bool
    findings: list[SecurityFinding]


class FrontendResult(BaseModel):
    score: int
    technologies_detected: list[str]
    findings: list[SecurityFinding]


class DependencyResult(BaseModel):
    score: int
    js_libraries: list[str]
    findings: list[SecurityFinding]


class BestPracticesResult(BaseModel):
    score: int
    security_txt_present: bool
    robots_txt_present: bool
    sourcemaps_found: list[str]
    findings: list[SecurityFinding]


SCORE_WEIGHTS: dict[str, int] = {
    "tls": 20,
    "headers": 20,
    "cookies": 10,
    "dns": 10,
    "frontend": 15,
    "dependencies": 15,
    "best_practices": 10,
}


class SecurityAuditResult(BaseModel):
    url: str
    overall_score: int
    headers: HeadersResult
    tls: TlsResult
    cookies: CookieResult
    dns: DnsResult
    frontend: FrontendResult
    dependencies: DependencyResult
    best_practices: BestPracticesResult
    all_findings: list[SecurityFinding]
    checked_with: str = "security-audit"
