from __future__ import annotations

import asyncio
from urllib.parse import urlparse

import httpx

from core.exceptions import ServiceMonitorError
from core.logging import logger
from slices.security.analyzers.best_practices import analyze_best_practices
from slices.security.analyzers.cookies import analyze_cookies
from slices.security.analyzers.dependencies import analyze_dependencies
from slices.security.analyzers.dns import analyze_dns
from slices.security.analyzers.frontend import analyze_frontend
from slices.security.analyzers.headers import analyze_headers
from slices.security.analyzers.tls import analyze_tls
from slices.security.schemas import SCORE_WEIGHTS, SecurityAuditResult, SecurityFinding


def _weighted_score(sub_scores: dict[str, int]) -> int:
    total_weight = sum(SCORE_WEIGHTS.values())
    weighted_sum = sum(sub_scores[key] * SCORE_WEIGHTS[key] for key in SCORE_WEIGHTS)
    return round(weighted_sum / total_weight)


async def check_security(client: httpx.AsyncClient, url: str, robots_txt_present: bool) -> SecurityAuditResult:
    logger.info("function=check_security | url=%s", url)

    try:
        response = await client.get(url)
    except httpx.TimeoutException:
        raise ServiceMonitorError(
            message=f"Security audit timed out for {url}",
            code="SECURITY_CHECK_TIMEOUT",
        )
    except httpx.HTTPError as exc:
        raise ServiceMonitorError(
            message=f"Security audit failed: {exc}",
            code="SECURITY_CHECK_FAILED",
        )

    html = response.text
    domain = urlparse(url).hostname or ""

    headers_result = analyze_headers(response.headers)
    cookies_result = analyze_cookies(response.headers)
    frontend_result = analyze_frontend(html, response.headers, url)
    dependencies_result = analyze_dependencies(html)

    tls_result, dns_result, best_practices_result = await asyncio.gather(
        analyze_tls(url),
        analyze_dns(domain),
        analyze_best_practices(client, url, html, robots_txt_present),
    )

    sub_scores = {
        "tls": tls_result.score,
        "headers": headers_result.score,
        "cookies": cookies_result.score,
        "dns": dns_result.score,
        "frontend": frontend_result.score,
        "dependencies": dependencies_result.score,
        "best_practices": best_practices_result.score,
    }
    overall = _weighted_score(sub_scores)

    all_findings: list[SecurityFinding] = (
        tls_result.findings
        + headers_result.findings
        + cookies_result.findings
        + dns_result.findings
        + frontend_result.findings
        + dependencies_result.findings
        + best_practices_result.findings
    )

    result = SecurityAuditResult(
        url=url,
        overall_score=overall,
        headers=headers_result,
        tls=tls_result,
        cookies=cookies_result,
        dns=dns_result,
        frontend=frontend_result,
        dependencies=dependencies_result,
        best_practices=best_practices_result,
        all_findings=all_findings,
    )

    logger.info(
        "function=check_security | result=overall_score=%s tls=%s headers=%s "
        "cookies=%s dns=%s frontend=%s dependencies=%s best_practices=%s",
        overall,
        tls_result.score,
        headers_result.score,
        cookies_result.score,
        dns_result.score,
        frontend_result.score,
        dependencies_result.score,
        best_practices_result.score,
    )
    return result
