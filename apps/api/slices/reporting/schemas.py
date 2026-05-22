from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from slices.accessibility.schemas import AccessibilityResult
from slices.ai_summary.schemas import AiSummary
from slices.discovery.schemas import DiscoveryResult
from slices.health_check.schemas import HealthCheckResult
from slices.scoring.schemas import ScoreBreakdown
from slices.security.schemas import SecurityAuditResult
from slices.seo.schemas import SeoAnalysisResult


class ReportFormat(str, Enum):
    json = "json"
    pdf = "pdf"
    csv = "csv"


class PageAuditResult(BaseModel):
    url: str
    health: HealthCheckResult | None = None
    seo: SeoAnalysisResult | None = None
    accessibility: AccessibilityResult | None = None
    security: SecurityAuditResult | None = None


class AuditReport(BaseModel):
    audit_id: str
    report_name: str
    root_url: str
    generated_at: str
    discovery: DiscoveryResult
    health: HealthCheckResult | None = None
    seo: SeoAnalysisResult | None = None
    accessibility: AccessibilityResult | None = None
    security: SecurityAuditResult | None = None
    score_breakdown: ScoreBreakdown
    page_results: list[PageAuditResult] = []
    format: ReportFormat = ReportFormat.json
    scope: list[str] = []  # checks that were included in this audit run
    ai_summary: AiSummary | None = None  # optional AI explanation layer; null unless requested
