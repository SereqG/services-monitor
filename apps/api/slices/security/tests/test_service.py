from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.exceptions import ServiceMonitorError
from slices.security.schemas import (
    BestPracticesResult,
    CookieResult,
    DependencyResult,
    DnsResult,
    FrontendResult,
    HeadersResult,
    SCORE_WEIGHTS,
    SecurityAuditResult,
    TlsResult,
)
from slices.security.service import _weighted_score, check_security


def _mock_response(html: str = "", headers: dict | None = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.text = html
    resp.headers = httpx.Headers(headers or {})
    return resp


def _sub_results(score: int = 100) -> dict:
    findings: list = []
    return {
        "headers": HeadersResult(score=score, headers_present=[], headers_missing=[], findings=findings),
        "tls": TlsResult(score=score, tls_version="TLSv1.3", certificate_valid=True, certificate_expiry_days=365, findings=findings),
        "cookies": CookieResult(score=score, total_cookies=0, findings=findings),
        "dns": DnsResult(score=score, spf_present=True, dmarc_present=True, dnssec_enabled=True, caa_present=True, findings=findings),
        "frontend": FrontendResult(score=score, technologies_detected=[], findings=findings),
        "dependencies": DependencyResult(score=score, js_libraries=[], findings=findings),
        "best_practices": BestPracticesResult(score=score, security_txt_present=True, robots_txt_present=True, sourcemaps_found=[], findings=findings),
    }


def _patch_all_analyzers(score: int = 100):
    sub = _sub_results(score)
    return [
        patch("slices.security.service.analyze_headers", return_value=sub["headers"]),
        patch("slices.security.service.analyze_cookies", return_value=sub["cookies"]),
        patch("slices.security.service.analyze_frontend", return_value=sub["frontend"]),
        patch("slices.security.service.analyze_dependencies", return_value=sub["dependencies"]),
        patch("slices.security.service.analyze_tls", new=AsyncMock(return_value=sub["tls"])),
        patch("slices.security.service.analyze_dns", new=AsyncMock(return_value=sub["dns"])),
        patch("slices.security.service.analyze_best_practices", new=AsyncMock(return_value=sub["best_practices"])),
    ]


def test_returns_security_audit_result():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.return_value = _mock_response()
    with (
        patch("slices.security.service.analyze_headers", return_value=_sub_results()["headers"]),
        patch("slices.security.service.analyze_cookies", return_value=_sub_results()["cookies"]),
        patch("slices.security.service.analyze_frontend", return_value=_sub_results()["frontend"]),
        patch("slices.security.service.analyze_dependencies", return_value=_sub_results()["dependencies"]),
        patch("slices.security.service.analyze_tls", new=AsyncMock(return_value=_sub_results()["tls"])),
        patch("slices.security.service.analyze_dns", new=AsyncMock(return_value=_sub_results()["dns"])),
        patch("slices.security.service.analyze_best_practices", new=AsyncMock(return_value=_sub_results()["best_practices"])),
    ):
        result = asyncio.run(check_security(client, "https://example.com", robots_txt_present=True))
    assert isinstance(result, SecurityAuditResult)
    assert result.url == "https://example.com"
    assert result.checked_with == "security-audit"


def test_all_sub_scores_100_gives_overall_100():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.return_value = _mock_response()
    patches = _patch_all_analyzers(100)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        result = asyncio.run(check_security(client, "https://example.com", robots_txt_present=True))
    assert result.overall_score == 100


def test_all_sub_scores_0_gives_overall_0():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.return_value = _mock_response()
    patches = _patch_all_analyzers(0)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        result = asyncio.run(check_security(client, "https://example.com", robots_txt_present=True))
    assert result.overall_score == 0


def test_timeout_raises_service_monitor_error():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.side_effect = httpx.TimeoutException("timed out")
    with pytest.raises(ServiceMonitorError) as exc_info:
        asyncio.run(check_security(client, "https://example.com", robots_txt_present=True))
    assert exc_info.value.code == "SECURITY_CHECK_TIMEOUT"
    assert "https://example.com" in exc_info.value.message


def test_http_error_raises_service_monitor_error():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.side_effect = httpx.ConnectError("connection refused")
    with pytest.raises(ServiceMonitorError) as exc_info:
        asyncio.run(check_security(client, "https://example.com", robots_txt_present=True))
    assert exc_info.value.code == "SECURITY_CHECK_FAILED"


def test_all_findings_aggregated_from_sub_results():
    from slices.security.schemas import SecurityFinding, Severity
    finding = SecurityFinding(
        category="headers", title="Missing X-Frame-Options",
        description="desc", severity=Severity.medium,
    )
    sub = _sub_results(100)
    sub["headers"] = HeadersResult(score=80, headers_present=[], headers_missing=["X-Frame-Options"], findings=[finding])

    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.return_value = _mock_response()
    with (
        patch("slices.security.service.analyze_headers", return_value=sub["headers"]),
        patch("slices.security.service.analyze_cookies", return_value=sub["cookies"]),
        patch("slices.security.service.analyze_frontend", return_value=sub["frontend"]),
        patch("slices.security.service.analyze_dependencies", return_value=sub["dependencies"]),
        patch("slices.security.service.analyze_tls", new=AsyncMock(return_value=sub["tls"])),
        patch("slices.security.service.analyze_dns", new=AsyncMock(return_value=sub["dns"])),
        patch("slices.security.service.analyze_best_practices", new=AsyncMock(return_value=sub["best_practices"])),
    ):
        result = asyncio.run(check_security(client, "https://example.com", robots_txt_present=True))
    assert finding in result.all_findings


def test_weighted_score_all_100():
    scores = {key: 100 for key in SCORE_WEIGHTS}
    assert _weighted_score(scores) == 100


def test_weighted_score_all_0():
    scores = {key: 0 for key in SCORE_WEIGHTS}
    assert _weighted_score(scores) == 0


def test_weighted_score_uses_doc_weights():
    scores = {key: 0 for key in SCORE_WEIGHTS}
    scores["tls"] = 100
    expected = round(100 * SCORE_WEIGHTS["tls"] / sum(SCORE_WEIGHTS.values()))
    assert _weighted_score(scores) == expected


def test_score_weights_sum_to_100():
    assert sum(SCORE_WEIGHTS.values()) == 100


def test_score_weights_match_doc_categories():
    expected_keys = {"tls", "headers", "cookies", "dns", "frontend", "dependencies", "best_practices"}
    assert set(SCORE_WEIGHTS.keys()) == expected_keys
