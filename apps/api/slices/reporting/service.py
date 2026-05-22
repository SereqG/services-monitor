from __future__ import annotations

from datetime import datetime, timezone

from core.logging import logger
from slices.accessibility.schemas import AccessibilityResult
from slices.discovery.schemas import DiscoveryResult
from slices.health_check.schemas import HealthCheckResult
from slices.reporting.schemas import AuditReport, PageAuditResult, ReportFormat
from slices.scoring.schemas import ScoreBreakdown
from slices.security.schemas import SecurityAuditResult
from slices.seo.schemas import SeoAnalysisResult


def assemble_report(
    audit_id: str,
    root_url: str,
    report_name: str,
    discovery: DiscoveryResult,
    score_breakdown: ScoreBreakdown,
    scope: list[str],
    health: HealthCheckResult | None = None,
    seo: SeoAnalysisResult | None = None,
    accessibility: AccessibilityResult | None = None,
    security: SecurityAuditResult | None = None,
    page_results: list[PageAuditResult] | None = None,
    fmt: ReportFormat = ReportFormat.json,
) -> AuditReport:
    logger.info("function=assemble_report | audit_id=%s root_url=%s report_name=%s pages=%s scope=%s", audit_id, root_url, report_name, len(page_results or []), scope)
    report = AuditReport(
        audit_id=audit_id,
        report_name=report_name,
        root_url=root_url,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        discovery=discovery,
        health=health,
        seo=seo,
        accessibility=accessibility,
        security=security,
        score_breakdown=score_breakdown,
        page_results=page_results or [],
        format=fmt,
        scope=scope,
    )
    logger.info(
        "function=assemble_report | result=report_name=%s generated_at=%s format=%s",
        report.report_name, report.generated_at, report.format,
    )
    return report
