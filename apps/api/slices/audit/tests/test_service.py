from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from slices.audit.schemas import AuditRequest
from slices.audit.service import run_audit
from slices.discovery.schemas import DiscoveredUrl, DiscoveryResult, RobotsPolicy
from slices.health_check.schemas import HealthCheckResult, HttpStatus
from slices.reporting.schemas import PageAuditResult
from slices.scoring.schemas import ScoreBreakdown
from slices.security.schemas import (
    BestPracticesResult,
    CookieResult,
    DependencyResult,
    DnsResult,
    FrontendResult,
    HeadersResult,
    SecurityAuditResult,
    TlsResult,
)


def _robots_policy() -> RobotsPolicy:
    return RobotsPolicy(
        fetched=True,
        allows_root=True,
        blocked_paths=[],
        sitemap_urls=[],
        raw=None,
    )


def _discovery(urls: list[DiscoveredUrl]) -> DiscoveryResult:
    allowed = [u for u in urls if u.status == "allowed"]
    return DiscoveryResult(
        root_url="https://example.com/",
        robots_policy=_robots_policy(),
        discovered_urls=urls,
        total_discovered=len(urls),
        total_allowed=len(allowed),
        hit_limit=False,
        duration_seconds=0.5,
    )


def _health(_client, url: str) -> HealthCheckResult:
    return HealthCheckResult(
        url=url,
        final_url=url,
        status_code=200,
        status=HttpStatus.ok,
        ttfb_ms=100.0,
        redirect_chain=[],
        has_redirect_loop=False,
        is_available=True,
    )


def _seo(_client, url: str):
    from slices.seo.schemas import HeadingStructure, MetaData, SeoAnalysisResult
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
        issues=[],
        score=100,
    )


def _a11y(_client, url: str):
    from slices.accessibility.schemas import AccessibilityResult
    return AccessibilityResult(url=url, issues=[], score=100, checked_with="html-heuristics")


def _security(_client, url: str, _robots: bool = False) -> SecurityAuditResult:
    empty_findings: list = []
    return SecurityAuditResult(
        url=url,
        overall_score=100,
        headers=HeadersResult(score=100, headers_present=[], headers_missing=[], findings=empty_findings),
        tls=TlsResult(score=100, tls_version="TLSv1.3", certificate_valid=True, certificate_expiry_days=365, findings=empty_findings),
        cookies=CookieResult(score=100, total_cookies=0, findings=empty_findings),
        dns=DnsResult(score=100, spf_present=True, dmarc_present=True, dnssec_enabled=True, caa_present=True, findings=empty_findings),
        frontend=FrontendResult(score=100, technologies_detected=[], findings=empty_findings),
        dependencies=DependencyResult(score=100, js_libraries=[], findings=empty_findings),
        best_practices=BestPracticesResult(score=100, security_txt_present=True, robots_txt_present=True, sourcemaps_found=[], findings=empty_findings),
        all_findings=empty_findings,
    )


def _score_mock() -> ScoreBreakdown:
    return ScoreBreakdown(overall_score=80, grade="B", categories=[])


def _patches(extra: dict | None = None):
    base = {
        "slices.audit.service.validate_url": patch("slices.audit.service.validate_url", return_value="https://example.com/"),
        "slices.audit.service.run_discovery": patch("slices.audit.service.run_discovery", new=AsyncMock()),
        "slices.audit.service.check_health": patch("slices.audit.service.check_health", new=AsyncMock(side_effect=_health)),
        "slices.audit.service.analyze_seo": patch("slices.audit.service.analyze_seo", new=AsyncMock(side_effect=_seo)),
        "slices.audit.service.analyze_accessibility": patch("slices.audit.service.analyze_accessibility", new=AsyncMock(side_effect=_a11y)),
        "slices.audit.service.check_security": patch("slices.audit.service.check_security", new=AsyncMock(side_effect=_security)),
        "slices.audit.service.calculate_score": patch("slices.audit.service.calculate_score", return_value=_score_mock()),
    }
    if extra:
        base.update(extra)
    return base


def test_page_results_populated_from_selected_urls():
    subpage = "https://example.com/about"
    discovered = [
        DiscoveredUrl(url="https://example.com/", depth=0, status="allowed"),
        DiscoveredUrl(url=subpage, depth=1, status="allowed"),
    ]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
        selected_urls=["https://example.com/", subpage],
    )
    patches = _patches({"slices.audit.service.run_discovery": patch(
        "slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))
    )})
    with patches["slices.audit.service.validate_url"], \
         patches["slices.audit.service.run_discovery"], \
         patches["slices.audit.service.check_health"], \
         patches["slices.audit.service.analyze_seo"], \
         patches["slices.audit.service.analyze_accessibility"], \
         patches["slices.audit.service.check_security"], \
         patches["slices.audit.service.calculate_score"]:
        report = asyncio.run(run_audit(MagicMock(), request))

    assert len(report.page_results) == 2
    assert report.page_results[0].url == "https://example.com/"
    assert report.page_results[1].url == subpage


def test_homepage_always_first_in_page_results():
    discovered = [
        DiscoveredUrl(url="https://example.com/", depth=0, status="allowed"),
    ]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
        selected_urls=["https://example.com/"],
    )
    patches = _patches({"slices.audit.service.run_discovery": patch(
        "slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))
    )})
    with patches["slices.audit.service.validate_url"], \
         patches["slices.audit.service.run_discovery"], \
         patches["slices.audit.service.check_health"], \
         patches["slices.audit.service.analyze_seo"], \
         patches["slices.audit.service.analyze_accessibility"], \
         patches["slices.audit.service.check_security"], \
         patches["slices.audit.service.calculate_score"]:
        report = asyncio.run(run_audit(MagicMock(), request))

    assert len(report.page_results) == 1
    assert report.page_results[0].url == "https://example.com/"


def test_blocked_urls_excluded_from_page_results():
    blocked = "https://example.com/private"
    allowed_sub = "https://example.com/about"
    discovered = [
        DiscoveredUrl(url="https://example.com/", depth=0, status="allowed"),
        DiscoveredUrl(url=allowed_sub, depth=1, status="allowed"),
        DiscoveredUrl(url=blocked, depth=1, status="blocked_by_robots"),
    ]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
        selected_urls=[allowed_sub, blocked],
    )
    patches = _patches({"slices.audit.service.run_discovery": patch(
        "slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))
    )})
    with patches["slices.audit.service.validate_url"], \
         patches["slices.audit.service.run_discovery"], \
         patches["slices.audit.service.check_health"], \
         patches["slices.audit.service.analyze_seo"], \
         patches["slices.audit.service.analyze_accessibility"], \
         patches["slices.audit.service.check_security"], \
         patches["slices.audit.service.calculate_score"]:
        report = asyncio.run(run_audit(MagicMock(), request))

    page_urls = [p.url for p in report.page_results]
    assert allowed_sub in page_urls
    assert blocked not in page_urls


def test_no_selected_urls_produces_homepage_only_page_results():
    discovered = [
        DiscoveredUrl(url="https://example.com/", depth=0, status="allowed"),
    ]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
    )
    patches = _patches({"slices.audit.service.run_discovery": patch(
        "slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))
    )})
    with patches["slices.audit.service.validate_url"], \
         patches["slices.audit.service.run_discovery"], \
         patches["slices.audit.service.check_health"], \
         patches["slices.audit.service.analyze_seo"], \
         patches["slices.audit.service.analyze_accessibility"], \
         patches["slices.audit.service.check_security"], \
         patches["slices.audit.service.calculate_score"]:
        report = asyncio.run(run_audit(MagicMock(), request))

    assert len(report.page_results) == 1
    assert report.page_results[0].url == "https://example.com/"


def test_performance_error_when_ttfb_unavailable():
    discovered = [DiscoveredUrl(url="https://example.com/", depth=0, status="allowed")]

    def _health_timeout(_client, url: str) -> HealthCheckResult:
        return HealthCheckResult(
            url=url,
            final_url=url,
            status_code=None,
            status=HttpStatus.timeout,
            ttfb_ms=None,
            redirect_chain=[],
            has_redirect_loop=False,
            is_available=False,
            error="Request timed out",
        )

    request = AuditRequest(url="https://example.com/", email="test@example.com")

    with (
        patch("slices.audit.service.validate_url", return_value="https://example.com/"),
        patch("slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))),
        patch("slices.audit.service.check_health", new=AsyncMock(side_effect=_health_timeout)),
        patch("slices.audit.service.analyze_seo", new=AsyncMock(side_effect=_seo)),
        patch("slices.audit.service.analyze_accessibility", new=AsyncMock(side_effect=_a11y)),
        patch("slices.audit.service.check_security", new=AsyncMock(side_effect=_security)),
    ):
        report = asyncio.run(run_audit(MagicMock(), request))

    perf = next(c for c in report.score_breakdown.categories if c.name == "performance")
    assert perf.status.value == "error"
    assert perf.score is None
    assert "TTFB" in perf.error


def test_scope_limits_checks_to_selected():
    discovered = [DiscoveredUrl(url="https://example.com/", depth=0, status="allowed")]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
        scope=["seo"],
    )
    with (
        patch("slices.audit.service.validate_url", return_value="https://example.com/"),
        patch("slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))),
        patch("slices.audit.service.check_health", new=AsyncMock(side_effect=_health)) as mock_health,
        patch("slices.audit.service.analyze_seo", new=AsyncMock(side_effect=_seo)) as mock_seo,
        patch("slices.audit.service.analyze_accessibility", new=AsyncMock(side_effect=_a11y)) as mock_a11y,
        patch("slices.audit.service.check_security", new=AsyncMock(side_effect=_security)) as mock_security,
    ):
        report = asyncio.run(run_audit(MagicMock(), request))

    mock_health.assert_not_called()
    mock_a11y.assert_not_called()
    mock_security.assert_not_called()
    mock_seo.assert_called_once()

    health_cat = next(c for c in report.score_breakdown.categories if c.name == "health")
    seo_cat = next(c for c in report.score_breakdown.categories if c.name == "seo")
    assert health_cat.status.value == "not_included"
    assert seo_cat.status.value == "ok"
    assert report.scope == ["seo"]


def test_not_included_categories_excluded_from_score():
    discovered = [DiscoveredUrl(url="https://example.com/", depth=0, status="allowed")]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
        scope=["health"],
    )
    patches = _patches({"slices.audit.service.run_discovery": patch(
        "slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))
    )})
    with patches["slices.audit.service.validate_url"], \
         patches["slices.audit.service.run_discovery"], \
         patches["slices.audit.service.check_health"], \
         patches["slices.audit.service.analyze_seo"], \
         patches["slices.audit.service.analyze_accessibility"], \
         patches["slices.audit.service.check_security"]:
        report = asyncio.run(run_audit(MagicMock(), request))

    not_included = [c for c in report.score_breakdown.categories if c.status.value == "not_included"]
    included = [c for c in report.score_breakdown.categories if c.status.value == "ok"]
    assert all(c.name in ("seo", "accessibility", "security") for c in not_included)
    assert all(c.name in ("health", "performance") for c in included)


def test_empty_scope_defaults_to_all_checks():
    discovered = [DiscoveredUrl(url="https://example.com/", depth=0, status="allowed")]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
        scope=None,
    )
    patches = _patches({"slices.audit.service.run_discovery": patch(
        "slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))
    )})
    with patches["slices.audit.service.validate_url"], \
         patches["slices.audit.service.run_discovery"], \
         patches["slices.audit.service.check_health"] as mock_health, \
         patches["slices.audit.service.analyze_seo"] as mock_seo, \
         patches["slices.audit.service.analyze_accessibility"] as mock_a11y, \
         patches["slices.audit.service.check_security"] as mock_security, \
         patches["slices.audit.service.calculate_score"]:
        asyncio.run(run_audit(MagicMock(), request))

    mock_health.assert_called_once()
    mock_seo.assert_called_once()
    mock_a11y.assert_called_once()
    mock_security.assert_called_once()


def test_security_included_in_subpage_results():
    subpage = "https://example.com/about"
    discovered = [
        DiscoveredUrl(url="https://example.com/", depth=0, status="allowed"),
        DiscoveredUrl(url=subpage, depth=1, status="allowed"),
    ]
    request = AuditRequest(
        url="https://example.com/",
        email="test@example.com",
        selected_urls=["https://example.com/", subpage],
    )
    patches = _patches({"slices.audit.service.run_discovery": patch(
        "slices.audit.service.run_discovery", new=AsyncMock(return_value=_discovery(discovered))
    )})
    with patches["slices.audit.service.validate_url"], \
         patches["slices.audit.service.run_discovery"], \
         patches["slices.audit.service.check_health"], \
         patches["slices.audit.service.analyze_seo"], \
         patches["slices.audit.service.analyze_accessibility"], \
         patches["slices.audit.service.check_security"], \
         patches["slices.audit.service.calculate_score"]:
        report = asyncio.run(run_audit(MagicMock(), request))

    assert len(report.page_results) == 2
    for page in report.page_results:
        assert page.security is not None
        assert page.security.overall_score == 100
