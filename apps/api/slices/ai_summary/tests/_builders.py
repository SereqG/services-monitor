"""Shared deterministic fixture builders for ai_summary tests."""

from __future__ import annotations

from slices.accessibility.schemas import AccessibilityIssue, AccessibilityResult
from slices.discovery.schemas import DiscoveredUrl, DiscoveryResult, RobotsPolicy
from slices.health_check.schemas import HealthCheckResult, HttpStatus
from slices.reporting.schemas import AuditReport, PageAuditResult
from slices.scoring.schemas import CategoryResult, CategoryStatus, ScoreBreakdown
from slices.seo.schemas import HeadingStructure, MetaData, SeoAnalysisResult, SeoIssue


def health(*, is_available: bool = True, has_redirect_loop: bool = False,
           ttfb_ms: float | None = 120.0) -> HealthCheckResult:
    return HealthCheckResult(
        url="https://example.com/",
        final_url="https://example.com/",
        status_code=200 if is_available else 500,
        status=HttpStatus.ok if is_available else HttpStatus.server_error,
        ttfb_ms=ttfb_ms,
        redirect_chain=[],
        has_redirect_loop=has_redirect_loop,
        is_available=is_available,
    )


def seo(url: str, score: int, issues: list[SeoIssue] | None = None) -> SeoAnalysisResult:
    return SeoAnalysisResult(
        url=url,
        meta=MetaData(
            title="Title", title_length=5, description=None, description_length=None,
            canonical=None, robots_meta=None, og_title=None, og_description=None, og_image=None,
        ),
        headings=HeadingStructure(h1_count=1, h2_count=0, h3_count=0, h1_texts=["Title"]),
        has_sitemap=False,
        has_schema_markup=False,
        images_without_alt=0,
        issues=issues or [],
        score=score,
    )


def seo_issue(message: str, severity: str = "medium", code: str = "SEO_X") -> SeoIssue:
    return SeoIssue(code=code, severity=severity, message=message)


def accessibility(url: str, score: int,
                  issues: list[AccessibilityIssue] | None = None) -> AccessibilityResult:
    return AccessibilityResult(
        url=url, issues=issues or [], score=score, checked_with="html-heuristics",
    )


def a11y_issue(message: str, severity: str = "moderate", code: str = "A11Y_X") -> AccessibilityIssue:
    return AccessibilityIssue(code=code, severity=severity, message=message)


def page(url: str, *, seo_score: int | None = None, accessibility_score: int | None = None,
         seo_issues: list[SeoIssue] | None = None,
         a11y_issues: list[AccessibilityIssue] | None = None,
         page_health: HealthCheckResult | None = None) -> PageAuditResult:
    return PageAuditResult(
        url=url,
        health=page_health,
        seo=seo(url, seo_score, seo_issues) if seo_score is not None else None,
        accessibility=(
            accessibility(url, accessibility_score, a11y_issues)
            if accessibility_score is not None
            else None
        ),
    )


def discovery() -> DiscoveryResult:
    return DiscoveryResult(
        root_url="https://example.com/",
        robots_policy=RobotsPolicy(
            fetched=True, allows_root=True, blocked_paths=[], sitemap_urls=[], raw=None,
        ),
        discovered_urls=[DiscoveredUrl(url="https://example.com/", depth=0, status="allowed")],
        total_discovered=1,
        total_allowed=1,
        hit_limit=False,
        duration_seconds=0.5,
    )


def report(pages: list[PageAuditResult], *, overall_score: int | None = 72,
           grade: str | None = "C", security=None, audit_id: str = "0" * 32) -> AuditReport:
    return AuditReport(
        audit_id=audit_id,
        report_name="Example",
        root_url="https://example.com/",
        generated_at="2026-05-21T10:00:00+00:00",
        discovery=discovery(),
        security=security,
        score_breakdown=ScoreBreakdown(
            categories=[CategoryResult(name="seo", score=overall_score, status=CategoryStatus.ok)],
            overall_score=overall_score,
            grade=grade,
        ),
        page_results=pages,
    )
