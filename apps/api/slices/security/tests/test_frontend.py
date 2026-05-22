from __future__ import annotations

import httpx

from slices.security.analyzers.frontend import analyze_frontend
from slices.security.schemas import Severity


def _headers(**kwargs: str) -> httpx.Headers:
    return httpx.Headers(kwargs)


def test_clean_page_gives_score_100():
    result = analyze_frontend("<html><body>hello</body></html>", _headers(), "https://example.com")
    assert result.score == 100
    assert result.findings == []
    assert result.technologies_detected == []


def test_detects_wordpress_from_html():
    html = '<html><body><link rel="stylesheet" href="/wp-content/themes/x.css"/></body></html>'
    result = analyze_frontend(html, _headers(), "https://example.com")
    assert "WordPress" in result.technologies_detected


def test_detects_nextjs_from_html():
    html = '<html><body><script id="__NEXT_DATA__" type="application/json">{}</script></body></html>'
    result = analyze_frontend(html, _headers(), "https://example.com")
    assert "Next.js" in result.technologies_detected


def test_detects_cloudflare_from_server_header():
    result = analyze_frontend("", _headers(server="cloudflare"), "https://example.com")
    assert "Cloudflare" in result.technologies_detected


def test_detects_nginx_from_server_header():
    result = analyze_frontend("", _headers(server="nginx/1.18.0"), "https://example.com")
    assert "nginx" in result.technologies_detected


def test_technology_findings_are_informational():
    html = '<html><body><script src="/wp-content/x.js"></script></body></html>'
    result = analyze_frontend(html, _headers(), "https://example.com")
    tech_findings = [f for f in result.findings if "Technology detected" in f.title]
    assert all(f.severity == Severity.informational for f in tech_findings)


def test_mixed_content_on_https_page_gives_medium_finding():
    html = '<html><body><img src="http://cdn.example.com/image.jpg"/></body></html>'
    result = analyze_frontend(html, _headers(), "https://example.com")
    mixed = [f for f in result.findings if "Mixed content" in f.title]
    assert len(mixed) == 1
    assert mixed[0].severity == Severity.medium


def test_http_resources_on_http_page_do_not_trigger_mixed_content():
    html = '<html><body><img src="http://cdn.example.com/image.jpg"/></body></html>'
    result = analyze_frontend(html, _headers(), "http://example.com")
    mixed = [f for f in result.findings if "Mixed content" in f.title]
    assert mixed == []


def test_score_reduced_by_mixed_content():
    html = '<html><body><img src="http://cdn.example.com/img.jpg"/></body></html>'
    result = analyze_frontend(html, _headers(), "https://example.com")
    assert result.score < 100


def test_score_not_below_zero():
    html = " ".join(f'<img src="http://bad.com/{i}.jpg"/>' for i in range(20))
    result = analyze_frontend(html, _headers(), "https://example.com")
    assert result.score >= 0


def test_findings_category_is_frontend():
    html = '<html><body><img src="http://x.com/y.jpg"/></body></html>'
    result = analyze_frontend(html, _headers(), "https://example.com")
    assert all(f.category == "frontend" for f in result.findings)
