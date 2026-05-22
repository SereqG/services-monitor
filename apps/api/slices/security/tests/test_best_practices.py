from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx

from slices.security.analyzers.best_practices import analyze_best_practices
from slices.security.schemas import Severity


def _mock_client(responses: dict[str, tuple[int, str]]) -> httpx.AsyncClient:
    client = MagicMock(spec=httpx.AsyncClient)

    async def _get(url: str, **kwargs):
        for path, (status_code, text) in responses.items():
            if url.endswith(path):
                resp = MagicMock(spec=httpx.Response)
                resp.status_code = status_code
                resp.text = text
                return resp
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 404
        resp.text = ""
        return resp

    client.get = AsyncMock(side_effect=_get)
    return client


def test_security_txt_present_no_finding():
    client = _mock_client({"/.well-known/security.txt": (200, "Contact: security@example.com")})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=True))
    assert result.security_txt_present is True
    assert not any("security.txt" in f.title for f in result.findings)


def test_security_txt_missing_gives_low_finding():
    client = _mock_client({})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=True))
    assert result.security_txt_present is False
    finding = next(f for f in result.findings if "security.txt" in f.title)
    assert finding.severity == Severity.low


def test_legacy_security_txt_path_is_tried():
    client = _mock_client({"/security.txt": (200, "Contact: security@example.com")})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=True))
    assert result.security_txt_present is True


def test_robots_txt_present_is_reflected():
    client = _mock_client({"/.well-known/security.txt": (200, "Contact: x@example.com")})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=True))
    assert result.robots_txt_present is True


def test_robots_txt_absent_is_reflected():
    client = _mock_client({"/.well-known/security.txt": (200, "Contact: x@example.com")})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=False))
    assert result.robots_txt_present is False


def test_sourcemap_in_html_gives_medium_finding():
    html = "//# sourceMappingURL=app.chunk.abc123.map"
    client = _mock_client({"/.well-known/security.txt": (200, "Contact: x@example.com")})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", html, robots_txt_present=True))
    assert "app.chunk.abc123.map" in result.sourcemaps_found
    sourcemap_finding = next(f for f in result.findings if "Source maps" in f.title)
    assert sourcemap_finding.severity == Severity.medium


def test_no_sourcemaps_in_clean_html():
    client = _mock_client({"/.well-known/security.txt": (200, "Contact: x@example.com")})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "<html></html>", robots_txt_present=True))
    assert result.sourcemaps_found == []


def test_http_error_on_security_txt_treated_as_absent():
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=False))
    assert result.security_txt_present is False


def test_score_100_when_all_best_practices_met():
    client = _mock_client({"/.well-known/security.txt": (200, "Contact: x@example.com")})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "<html></html>", robots_txt_present=True))
    assert result.score == 100


def test_score_reduced_for_missing_security_txt():
    client = _mock_client({})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=True))
    assert result.score < 100


def test_findings_category_is_best_practices():
    client = _mock_client({})
    result = asyncio.run(analyze_best_practices(client, "https://example.com", "", robots_txt_present=False))
    assert all(f.category == "best_practices" for f in result.findings)
