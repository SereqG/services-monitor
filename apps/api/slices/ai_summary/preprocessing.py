from __future__ import annotations

import statistics
from collections import Counter

from core.logging import logger
from slices.ai_summary.schemas import (
    AiAnalysisDataset,
    CategorySummary,
    GeneralInfo,
    ProblematicPage,
)
from slices.health_check.schemas import HealthCheckResult
from slices.reporting.schemas import AuditReport, PageAuditResult

PRIORITY_THRESHOLD = 70
MAX_PROBLEMATIC_PAGES = 10
MAX_COMMON_ISSUES = 5
MAX_PAGE_TOP_ISSUES = 6

# Maps both SEO and accessibility severity vocabularies onto a single ordering.
_SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "serious": 1,
    "medium": 2,
    "moderate": 2,
    "low": 3,
    "minor": 3,
    "info": 4,
    "informational": 4,
}
_UNKNOWN_SEVERITY_RANK = 5


def consistency_score(scores: list[int]) -> int:
    """100 minus the population standard deviation of page scores, clamped 0-100.

    Higher means scores are stable across pages. 0 or 1 scores -> 100 (no spread).
    """
    if len(scores) <= 1:
        return 100
    deviation = statistics.pstdev(scores)
    return max(0, min(100, 100 - round(deviation)))


def _health_page_score(health: HealthCheckResult) -> int:
    """Per-page health score. Mirrors the deterministic formula in audit/service.py."""
    score = 100 if health.is_available else 0
    if health.has_redirect_loop:
        score = max(0, score - 30)
    return score


def _health_messages(health: HealthCheckResult) -> list[str]:
    messages: list[str] = []
    if not health.is_available:
        messages.append("Page is not reachable")
    if health.has_redirect_loop:
        messages.append("Redirect loop detected")
    return messages


def _common_issues(messages: list[str], limit: int = MAX_COMMON_ISSUES) -> list[str]:
    """Most frequent issue messages, ranked by count desc then message asc."""
    counts = Counter(message for message in messages if message)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [message for message, _ in ranked[:limit]]


def _severity_rank(severity: str) -> int:
    return _SEVERITY_RANK.get(severity.lower(), _UNKNOWN_SEVERITY_RANK)


def _page_top_issues(page: PageAuditResult, limit: int = MAX_PAGE_TOP_ISSUES) -> list[str]:
    """Highest-severity issue messages for a single page, deduplicated."""
    ranked: list[tuple[int, str]] = []
    if page.seo:
        ranked += [(_severity_rank(i.severity), i.message) for i in page.seo.issues]
    if page.accessibility:
        ranked += [(_severity_rank(i.severity), i.message) for i in page.accessibility.issues]
    ranked.sort(key=lambda item: (item[0], item[1]))

    seen: set[str] = set()
    result: list[str] = []
    for _, message in ranked:
        if message and message not in seen:
            seen.add(message)
            result.append(message)
        if len(result) >= limit:
            break
    return result


def _build_categories(report: AuditReport) -> dict[str, CategorySummary]:
    """Per-category aggregates computed across every audited page."""
    pages = report.page_results
    categories: dict[str, CategorySummary] = {}

    health_scores = [_health_page_score(p.health) for p in pages if p.health]
    if health_scores:
        health_messages: list[str] = []
        for page in pages:
            if page.health:
                health_messages += _health_messages(page.health)
        categories["health"] = CategorySummary(
            average_score=round(statistics.mean(health_scores)),
            consistency=consistency_score(health_scores),
            common_issues=_common_issues(health_messages),
        )

    seo_scores = [p.seo.score for p in pages if p.seo]
    if seo_scores:
        seo_messages = [i.message for p in pages if p.seo for i in p.seo.issues]
        categories["seo"] = CategorySummary(
            average_score=round(statistics.mean(seo_scores)),
            consistency=consistency_score(seo_scores),
            common_issues=_common_issues(seo_messages),
        )

    accessibility_scores = [p.accessibility.score for p in pages if p.accessibility]
    if accessibility_scores:
        accessibility_messages = [
            i.message for p in pages if p.accessibility for i in p.accessibility.issues
        ]
        categories["accessibility"] = CategorySummary(
            average_score=round(statistics.mean(accessibility_scores)),
            consistency=consistency_score(accessibility_scores),
            common_issues=_common_issues(accessibility_messages),
        )

    # Security is audited once on the root URL, so it has no cross-page spread.
    if report.security is not None:
        categories["security"] = CategorySummary(
            average_score=report.security.overall_score,
            consistency=100,
            common_issues=_common_issues(
                [finding.title for finding in report.security.all_findings]
            ),
        )

    return categories


def rank_problematic_pages(
    pages: list[PageAuditResult],
    global_seo_avg: float,
    global_accessibility_avg: float,
    limit: int = MAX_PROBLEMATIC_PAGES,
) -> list[ProblematicPage]:
    """Worst pages by weakness relative to the audit-wide SEO/accessibility averages.

    weakness = max(0, seo_avg - page_seo) + max(0, accessibility_avg - page_accessibility)

    A missing per-page score contributes 0. Pages at or above average (weakness 0)
    are excluded. Sorted worst-first, URL-ascending as a stable tie-break.
    """
    ranked: list[ProblematicPage] = []
    for page in pages:
        seo_score = page.seo.score if page.seo else None
        accessibility_score = page.accessibility.score if page.accessibility else None
        seo_gap = max(0.0, global_seo_avg - seo_score) if seo_score is not None else 0.0
        accessibility_gap = (
            max(0.0, global_accessibility_avg - accessibility_score)
            if accessibility_score is not None
            else 0.0
        )
        weakness = round(seo_gap + accessibility_gap)
        if weakness <= 0:
            continue
        ranked.append(
            ProblematicPage(
                url=page.url,
                weakness_score=weakness,
                seo_score=seo_score,
                accessibility_score=accessibility_score,
                health_available=page.health.is_available if page.health else None,
                top_issues=_page_top_issues(page),
            )
        )
    ranked.sort(key=lambda page: (-page.weakness_score, page.url))
    return ranked[:limit]


def build_ai_dataset(report: AuditReport, audit_id: str) -> AiAnalysisDataset:
    """Deterministically transform an AuditReport into the curated LLM context dataset.

    No AI is used here — only aggregation, ranking and noise reduction.
    """
    logger.info(
        "function=build_ai_dataset | audit_id=%s root_url=%s pages=%s",
        audit_id,
        report.root_url,
        len(report.page_results),
    )
    categories = _build_categories(report)

    priority_areas = [
        name
        for name, _ in sorted(
            (
                (name, summary.average_score)
                for name, summary in categories.items()
                if summary.average_score < PRIORITY_THRESHOLD
            ),
            key=lambda item: item[1],
        )
    ]

    seo_scores = [p.seo.score for p in report.page_results if p.seo]
    accessibility_scores = [
        p.accessibility.score for p in report.page_results if p.accessibility
    ]
    global_seo_avg = statistics.mean(seo_scores) if seo_scores else 0.0
    global_accessibility_avg = (
        statistics.mean(accessibility_scores) if accessibility_scores else 0.0
    )

    problematic_pages = rank_problematic_pages(
        report.page_results, global_seo_avg, global_accessibility_avg
    )

    general_info = GeneralInfo(
        overall_score=report.score_breakdown.overall_score,
        grade=report.score_breakdown.grade,
        categories=categories,
        priority_areas=priority_areas,
        problematic_pages=problematic_pages,
    )
    logger.info(
        "function=build_ai_dataset | result=audit_id=%s categories=%s "
        "priority_areas=%s problematic_pages=%s",
        audit_id,
        sorted(categories),
        priority_areas,
        len(problematic_pages),
    )
    return AiAnalysisDataset(
        audit_id=audit_id,
        root_url=report.root_url,
        generated_at=report.generated_at,
        general_info=general_info,
    )
