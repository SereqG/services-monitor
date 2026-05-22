from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from slices.discovery.schemas import UrlStatus
from slices.discovery.service import is_blocked_by_robots, parse_robots_txt, run_discovery


def test_parse_robots_blocks_path():
    content = "User-agent: *\nDisallow: /admin\n"
    policy = parse_robots_txt(content)
    assert "/admin" in policy.blocked_paths
    assert policy.allows_root is True


def test_parse_robots_blocks_root():
    content = "User-agent: *\nDisallow: /\n"
    policy = parse_robots_txt(content)
    assert policy.allows_root is False


def test_parse_robots_extracts_sitemap():
    content = "Sitemap: https://example.com/sitemap.xml\n"
    policy = parse_robots_txt(content)
    assert "https://example.com/sitemap.xml" in policy.sitemap_urls


def test_parse_robots_ignores_irrelevant_agent():
    content = "User-agent: Googlebot\nDisallow: /secret\n"
    policy = parse_robots_txt(content)
    assert "/secret" not in policy.blocked_paths


def test_is_blocked_matches_prefix():
    assert is_blocked_by_robots("/admin/users", ["/admin"]) is True


def test_is_not_blocked():
    assert is_blocked_by_robots("/about", ["/admin"]) is False


def test_empty_blocked_paths_allows_all():
    assert is_blocked_by_robots("/anything", []) is False


@pytest.mark.asyncio
async def test_run_discovery_records_fetch_error():
    """A URL that raises httpx.HTTPError must appear as fetch_error, not be silently dropped."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.side_effect = [
        httpx.ConnectError("connection refused"),  # robots.txt fetch
        httpx.ConnectError("connection refused"),  # root URL fetch
    ]

    result = await run_discovery(client, "https://unreachable.example.com")

    assert result.total_allowed == 0
    assert result.total_discovered == 1
    assert result.discovered_urls[0].status == UrlStatus.fetch_error
    assert result.discovered_urls[0].url == "https://unreachable.example.com"


@pytest.mark.asyncio
async def test_run_discovery_single_page_site():
    """A single-page site with no links returns exactly 1 allowed URL."""
    robots_response = MagicMock()
    robots_response.status_code = 404

    root_response = MagicMock()
    root_response.status_code = 200
    root_response.text = "<html><body><h1>Hello</h1></body></html>"

    client = AsyncMock(spec=httpx.AsyncClient)
    client.get.side_effect = [robots_response, root_response]

    result = await run_discovery(client, "https://example.com")

    assert result.total_allowed == 1
    assert result.total_discovered == 1
    assert result.discovered_urls[0].status == UrlStatus.allowed
    assert result.discovered_urls[0].url == "https://example.com"
