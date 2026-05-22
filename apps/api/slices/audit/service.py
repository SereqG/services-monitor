from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator

import httpx

from core.config import settings
from core.logging import logger
from slices.accessibility.service import analyze_accessibility
from slices.ai_summary.schemas import AiSummary, AiSummaryStatus
from slices.ai_summary.service import safe_generate_ai_summary
from slices.audit.schemas import ALL_CHECKS, AuditEvent, AuditEventType, AuditRequest
from slices.discovery.service import run_discovery
from slices.health_check.service import check_health
from slices.input_validation.service import validate_url
from slices.reporting.schemas import AuditReport, PageAuditResult
from slices.reporting.service import assemble_report
from slices.scoring.schemas import CategoryResult, CategoryStatus
from slices.scoring.service import calculate_score
from slices.security.schemas import SecurityAuditResult
from slices.security.service import check_security
from slices.seo.service import analyze_seo
from slices.summaries.storage import save_summary


def _ttfb_to_score(ttfb_ms: float) -> int:
    if ttfb_ms < 200:
        return 100
    if ttfb_ms < 500:
        return 80
    if ttfb_ms < 800:
        return 60
    if ttfb_ms < 1500:
        return 40
    return 20


async def _safe_check_security(
    client: httpx.AsyncClient, url: str, robots_txt_present: bool
) -> SecurityAuditResult | Exception:
    try:
        return await check_security(client, url, robots_txt_present)
    except Exception as exc:
        return exc


async def _audit_page(
    client: httpx.AsyncClient, page_url: str, scope: frozenset[str], robots_txt_present: bool = False
) -> PageAuditResult:
    tasks: list[tuple[str, object]] = []
    if "health" in scope:
        tasks.append(("health", check_health(client, page_url)))
    if "seo" in scope:
        tasks.append(("seo", analyze_seo(client, page_url)))
    if "accessibility" in scope:
        tasks.append(("accessibility", analyze_accessibility(client, page_url)))
    if "security" in scope:
        tasks.append(("security", _safe_check_security(client, page_url, robots_txt_present)))

    if tasks:
        keys, coros = zip(*tasks)
        results = await asyncio.gather(*coros)
        result_map = dict(zip(keys, results))
    else:
        result_map = {}

    security_raw = result_map.get("security")
    page_security: SecurityAuditResult | None = (
        security_raw if security_raw is not None and not isinstance(security_raw, Exception) else None
    )

    return PageAuditResult(
        url=page_url,
        health=result_map.get("health"),
        seo=result_map.get("seo"),
        accessibility=result_map.get("accessibility"),
        security=page_security,
    )


async def _generate_ai_summary(
    client: httpx.AsyncClient, report: AuditReport, audit_id: str
) -> AiSummary:
    """Run the optional AI explanation layer, respecting server configuration.

    AI is non-critical: a missing API key or disabled feature yields an explicit
    error summary rather than failing the audit.
    """
    if settings.ai_summary_enabled and settings.openrouter_api_key:
        return await safe_generate_ai_summary(client, report, audit_id)
    logger.info(
        "function=_generate_ai_summary | audit_id=%s status=error reason=not_configured",
        audit_id,
    )
    return AiSummary(
        status=AiSummaryStatus.error,
        audit_id=audit_id,
        error="AI summary is not configured on this server.",
    )


async def run_audit(client: httpx.AsyncClient, request: AuditRequest) -> AuditReport:
    """Orchestrates the full audit workflow across all slices."""
    logger.info(
        "function=run_audit | url=%s report_name=%s scope=%s ai_summary=%s",
        request.url,
        request.report_name,
        request.scope,
        request.enable_ai_summary,
    )
    url = validate_url(request.url)
    audit_id = uuid.uuid4().hex

    effective_scope: frozenset[str] = (
        frozenset(request.scope) if request.scope else frozenset(ALL_CHECKS)
    )

    if request.discovery_result is not None:
        discovery = request.discovery_result
        logger.info("function=run_audit | discovery=reused urls=%s", discovery.total_discovered)
    else:
        discovery = await run_discovery(client, url, max_urls=request.max_sites, max_depth=request.max_depth)

    tasks: list[tuple[str, object]] = []
    if "health" in effective_scope:
        tasks.append(("health", check_health(client, url)))
    if "seo" in effective_scope:
        tasks.append(("seo", analyze_seo(client, url)))
    if "accessibility" in effective_scope:
        tasks.append(("accessibility", analyze_accessibility(client, url)))
    if "security" in effective_scope:
        tasks.append(("security", _safe_check_security(client, url, discovery.robots_policy.fetched)))

    if tasks:
        keys, coros = zip(*tasks)
        gathered = await asyncio.gather(*coros)
        result_map = dict(zip(keys, gathered))
    else:
        result_map = {}

    health = result_map.get("health")
    seo = result_map.get("seo")
    accessibility = result_map.get("accessibility")
    security_raw = result_map.get("security")

    categories: list[CategoryResult] = []

    if "health" in effective_scope and health is not None:
        health_score = 100 if health.is_available else 0
        if health.has_redirect_loop:
            health_score = max(0, health_score - 30)
        categories.append(
            CategoryResult(name="health", score=health_score, status=CategoryStatus.ok)
        )

        if health.ttfb_ms is not None:
            perf_category = CategoryResult(
                name="performance",
                score=_ttfb_to_score(health.ttfb_ms),
                status=CategoryStatus.ok,
            )
        else:
            reason = health.error or f"HTTP status: {health.status}"
            perf_category = CategoryResult(
                name="performance",
                score=None,
                status=CategoryStatus.error,
                error=f"Performance score unavailable — could not measure TTFB: {reason}",
            )
        categories.append(perf_category)
    else:
        categories.append(
            CategoryResult(name="health", score=None, status=CategoryStatus.not_included)
        )
        categories.append(
            CategoryResult(name="performance", score=None, status=CategoryStatus.not_included)
        )

    if "seo" in effective_scope and seo is not None:
        categories.append(CategoryResult(name="seo", score=seo.score, status=CategoryStatus.ok))
    else:
        categories.append(
            CategoryResult(name="seo", score=None, status=CategoryStatus.not_included)
        )

    if "accessibility" in effective_scope and accessibility is not None:
        categories.append(
            CategoryResult(
                name="accessibility", score=accessibility.score, status=CategoryStatus.ok
            )
        )
    else:
        categories.append(
            CategoryResult(name="accessibility", score=None, status=CategoryStatus.not_included)
        )

    if "security" in effective_scope:
        if isinstance(security_raw, Exception):
            security_category = CategoryResult(
                name="security",
                score=None,
                status=CategoryStatus.error,
                error=str(security_raw),
            )
            security_detail: SecurityAuditResult | None = None
        else:
            security_category = CategoryResult(
                name="security",
                score=security_raw.overall_score,
                status=CategoryStatus.ok,
            )
            security_detail = security_raw
    else:
        security_category = CategoryResult(
            name="security", score=None, status=CategoryStatus.not_included
        )
        security_detail = None
    categories.append(security_category)

    score_breakdown = calculate_score(categories)

    page_results: list[PageAuditResult] = [PageAuditResult(url=url, health=health, seo=seo, accessibility=accessibility, security=security_detail)]
    if request.selected_urls:
        allowed_urls = {u.url for u in discovery.discovered_urls if u.status == "allowed"}
        subpages = [u for u in request.selected_urls if u != url and u in allowed_urls]
        if subpages:
            logger.info("function=run_audit | auditing subpages count=%s", len(subpages))
            for i, subpage_url in enumerate(subpages):
                if i > 0:
                    await asyncio.sleep(3)
                try:
                    page_results.append(await _audit_page(client, subpage_url, effective_scope, discovery.robots_policy.fetched))
                except Exception as exc:
                    logger.error("function=run_audit | subpage_audit_failed url=%s error=%s", subpage_url, exc)

    report = assemble_report(
        audit_id=audit_id,
        root_url=url,
        report_name=request.report_name or url,
        discovery=discovery,
        score_breakdown=score_breakdown,
        scope=sorted(effective_scope),
        health=health,
        seo=seo,
        accessibility=accessibility,
        security=security_detail,
        page_results=page_results,
    )
    logger.info(
        "function=run_audit | result=score=%s grade=%s pages_discovered=%s seo_score=%s "
        "accessibility_score=%s security_score=%s subpages_audited=%s scope=%s",
        score_breakdown.overall_score,
        score_breakdown.grade,
        discovery.total_discovered,
        seo.score if seo else None,
        accessibility.score if accessibility else None,
        security_category.score,
        len(page_results),
        sorted(effective_scope),
    )

    if request.enable_ai_summary:
        report.ai_summary = await _generate_ai_summary(client, report, audit_id)

    save_summary(report)
    return report


def _elapsed(start: float) -> float:
    return round(time.monotonic() - start, 1)


async def stream_audit(
    client: httpx.AsyncClient, request: AuditRequest
) -> AsyncGenerator[AuditEvent, None]:
    """Runs the full audit workflow and yields AuditEvent progress events."""
    logger.info("function=stream_audit | url=%s scope=%s", request.url, request.scope)
    start = time.monotonic()

    url = validate_url(request.url)
    audit_id = uuid.uuid4().hex
    effective_scope: frozenset[str] = (
        frozenset(request.scope) if request.scope else frozenset(ALL_CHECKS)
    )

    yield AuditEvent(
        type=AuditEventType.phase,
        message=f"Starting audit for {url}",
        elapsed_seconds=0.0,
        max_duration_seconds=settings.audit_max_duration_seconds,
    )

    if request.discovery_result is not None:
        discovery = request.discovery_result
        logger.info("function=stream_audit | discovery=reused urls=%s", discovery.total_discovered)
        yield AuditEvent(
            type=AuditEventType.phase,
            message=f"Using previous discovery — {discovery.total_allowed} page(s) found",
            elapsed_seconds=_elapsed(start),
        )
    else:
        yield AuditEvent(
            type=AuditEventType.phase,
            message="Running site discovery, please wait…",
            elapsed_seconds=_elapsed(start),
        )
        discovery = await run_discovery(client, url, max_urls=request.max_sites, max_depth=request.max_depth)
        yield AuditEvent(
            type=AuditEventType.phase,
            message=f"Discovery complete — {discovery.total_allowed} page(s) found",
            elapsed_seconds=_elapsed(start),
        )

    check_labels: list[tuple[str, str]] = []
    if "health" in effective_scope:
        check_labels.append(("health", "health check"))
    if "seo" in effective_scope:
        check_labels.append(("seo", "SEO analysis"))
    if "accessibility" in effective_scope:
        check_labels.append(("accessibility", "accessibility check"))
    if "security" in effective_scope:
        check_labels.append(("security", "security audit"))

    for _, label in check_labels:
        yield AuditEvent(
            type=AuditEventType.phase,
            message=f"Running {label}…",
            elapsed_seconds=_elapsed(start),
        )

    tasks: list[tuple[str, object]] = []
    if "health" in effective_scope:
        tasks.append(("health", check_health(client, url)))
    if "seo" in effective_scope:
        tasks.append(("seo", analyze_seo(client, url)))
    if "accessibility" in effective_scope:
        tasks.append(("accessibility", analyze_accessibility(client, url)))
    if "security" in effective_scope:
        tasks.append(("security", _safe_check_security(client, url, discovery.robots_policy.fetched)))

    if tasks:
        keys, coros = zip(*tasks)
        gathered = await asyncio.gather(*coros)
        result_map = dict(zip(keys, gathered))
    else:
        result_map = {}

    for _, label in check_labels:
        yield AuditEvent(
            type=AuditEventType.phase,
            message=f"{label.capitalize()} complete",
            elapsed_seconds=_elapsed(start),
        )

    health = result_map.get("health")
    seo = result_map.get("seo")
    accessibility = result_map.get("accessibility")
    security_raw = result_map.get("security")

    categories: list[CategoryResult] = []

    if "health" in effective_scope and health is not None:
        health_score = 100 if health.is_available else 0
        if health.has_redirect_loop:
            health_score = max(0, health_score - 30)
        categories.append(
            CategoryResult(name="health", score=health_score, status=CategoryStatus.ok)
        )

        if health.ttfb_ms is not None:
            perf_category = CategoryResult(
                name="performance",
                score=_ttfb_to_score(health.ttfb_ms),
                status=CategoryStatus.ok,
            )
        else:
            reason = health.error or f"HTTP status: {health.status}"
            perf_category = CategoryResult(
                name="performance",
                score=None,
                status=CategoryStatus.error,
                error=f"Performance score unavailable — could not measure TTFB: {reason}",
            )
        categories.append(perf_category)
    else:
        categories.append(
            CategoryResult(name="health", score=None, status=CategoryStatus.not_included)
        )
        categories.append(
            CategoryResult(name="performance", score=None, status=CategoryStatus.not_included)
        )

    if "seo" in effective_scope and seo is not None:
        categories.append(CategoryResult(name="seo", score=seo.score, status=CategoryStatus.ok))
    else:
        categories.append(
            CategoryResult(name="seo", score=None, status=CategoryStatus.not_included)
        )

    if "accessibility" in effective_scope and accessibility is not None:
        categories.append(
            CategoryResult(
                name="accessibility", score=accessibility.score, status=CategoryStatus.ok
            )
        )
    else:
        categories.append(
            CategoryResult(name="accessibility", score=None, status=CategoryStatus.not_included)
        )

    if "security" in effective_scope:
        if isinstance(security_raw, Exception):
            security_category = CategoryResult(
                name="security",
                score=None,
                status=CategoryStatus.error,
                error=str(security_raw),
            )
            security_detail: SecurityAuditResult | None = None
        else:
            security_category = CategoryResult(
                name="security",
                score=security_raw.overall_score,
                status=CategoryStatus.ok,
            )
            security_detail = security_raw
    else:
        security_category = CategoryResult(
            name="security", score=None, status=CategoryStatus.not_included
        )
        security_detail = None
    categories.append(security_category)

    yield AuditEvent(
        type=AuditEventType.phase,
        message="Calculating scores…",
        elapsed_seconds=_elapsed(start),
    )
    score_breakdown = calculate_score(categories)

    page_results: list[PageAuditResult] = [PageAuditResult(url=url, health=health, seo=seo, accessibility=accessibility, security=security_detail)]
    if request.selected_urls:
        allowed_urls = {u.url for u in discovery.discovered_urls if u.status == "allowed"}
        subpages = [u for u in request.selected_urls if u != url and u in allowed_urls]
        if subpages:
            for i, subpage_url in enumerate(subpages):
                if i > 0:
                    await asyncio.sleep(3)
                yield AuditEvent(
                    type=AuditEventType.phase,
                    message=f"Auditing subpage: {subpage_url}",
                    elapsed_seconds=_elapsed(start),
                )
                try:
                    page_results.append(await _audit_page(client, subpage_url, effective_scope, discovery.robots_policy.fetched))
                except Exception as exc:
                    logger.error("function=stream_audit | subpage_audit_failed url=%s error=%s", subpage_url, exc)

    yield AuditEvent(
        type=AuditEventType.phase,
        message="Assembling report…",
        elapsed_seconds=_elapsed(start),
    )
    report = assemble_report(
        audit_id=audit_id,
        root_url=url,
        report_name=request.report_name or url,
        discovery=discovery,
        score_breakdown=score_breakdown,
        scope=sorted(effective_scope),
        health=health,
        seo=seo,
        accessibility=accessibility,
        security=security_detail,
        page_results=page_results,
    )
    logger.info(
        "function=stream_audit | result=score=%s grade=%s pages_discovered=%s subpages_audited=%s scope=%s",
        score_breakdown.overall_score,
        score_breakdown.grade,
        discovery.total_discovered,
        len(page_results),
        sorted(effective_scope),
    )

    if request.enable_ai_summary:
        yield AuditEvent(
            type=AuditEventType.phase,
            message="Generating AI summary…",
            elapsed_seconds=_elapsed(start),
        )
        report.ai_summary = await _generate_ai_summary(client, report, audit_id)
        if report.ai_summary.status == AiSummaryStatus.ok:
            yield AuditEvent(
                type=AuditEventType.phase,
                message="AI summary ready",
                elapsed_seconds=_elapsed(start),
            )
        else:
            yield AuditEvent(
                type=AuditEventType.phase,
                message=f"AI summary unavailable — {report.ai_summary.error}",
                elapsed_seconds=_elapsed(start),
            )

    save_summary(report)
    yield AuditEvent(type=AuditEventType.complete, message="Audit complete", result=report)
