from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import AsyncGenerator
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from core.config import settings
from core.logging import logger
from slices.discovery.schemas import DiscoveredUrl, DiscoveryEvent, DiscoveryEventType, DiscoveryResult, RobotsPolicy, UrlStatus


def parse_robots_txt(content: str) -> RobotsPolicy:
    """Parses robots.txt text into a structured RobotsPolicy."""
    logger.info("function=parse_robots_txt | content_length=%s", len(content))
    blocked_paths: list[str] = []
    sitemap_urls: list[str] = []
    current_agent_applies = False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        lower = line.lower()
        if lower.startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            current_agent_applies = agent in ("*", "ServiceMonitorBot")
        elif current_agent_applies and lower.startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path:
                blocked_paths.append(path)
        elif lower.startswith("sitemap:"):
            url = line.split(":", 1)[1].strip()
            if url:
                sitemap_urls.append(url)

    allows_root = not any(p == "/" for p in blocked_paths)

    result = RobotsPolicy(
        fetched=True,
        allows_root=allows_root,
        blocked_paths=blocked_paths,
        sitemap_urls=sitemap_urls,
        raw=content,
    )
    logger.info(
        "function=parse_robots_txt | result=allows_root=%s blocked_paths=%s sitemaps=%s",
        result.allows_root, len(result.blocked_paths), len(result.sitemap_urls),
    )
    return result


def is_blocked_by_robots(path: str, blocked_paths: list[str]) -> bool:
    logger.info("function=is_blocked_by_robots | path=%s blocked_paths_count=%s", path, len(blocked_paths))
    result = any(path.startswith(blocked) for blocked in blocked_paths)
    logger.info("function=is_blocked_by_robots | result=%s", result)
    return result


def is_same_domain(url: str, root_url: str) -> bool:
    logger.info("function=is_same_domain | url=%s root_url=%s", url, root_url)
    result = urlparse(url).netloc == urlparse(root_url).netloc
    logger.info("function=is_same_domain | result=%s", result)
    return result


async def fetch_robots_txt(client: httpx.AsyncClient, root_url: str) -> RobotsPolicy:
    robots_url = urljoin(root_url, "/robots.txt")
    logger.info("function=fetch_robots_txt | robots_url=%s", robots_url)
    try:
        response = await client.get(robots_url)
        if response.status_code == 200:
            logger.info("function=fetch_robots_txt | result=fetched status_code=200")
            return parse_robots_txt(response.text)
        logger.info("function=fetch_robots_txt | result=not_found status_code=%s", response.status_code)
    except httpx.HTTPError as exc:
        logger.info("function=fetch_robots_txt | result=error error=%s", exc)

    policy = RobotsPolicy(fetched=False, allows_root=True, blocked_paths=[], sitemap_urls=[])
    logger.info("function=fetch_robots_txt | result=fallback fetched=False allows_root=True")
    return policy


async def run_discovery(
    client: httpx.AsyncClient,
    root_url: str,
    max_urls: int | None = None,
    max_depth: int | None = None,
) -> DiscoveryResult:
    """BFS crawl bounded by hard caps defined in settings (or lower user-supplied limits)."""
    effective_max_urls = min(max_urls, settings.discovery_max_urls) if max_urls is not None else settings.discovery_max_urls
    effective_max_depth = min(max_depth, settings.discovery_max_depth) if max_depth is not None else settings.discovery_max_depth
    logger.info(
        "function=run_discovery | url=%s max_urls=%s max_depth=%s",
        root_url, effective_max_urls, effective_max_depth,
    )
    start = time.monotonic()
    robots = await fetch_robots_txt(client, root_url)

    discovered: list[DiscoveredUrl] = []
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(root_url, 0)])
    request_count = 0

    while queue:
        elapsed = time.monotonic() - start
        if (
            len(discovered) >= effective_max_urls
            or request_count >= settings.discovery_max_requests
            or elapsed > settings.discovery_max_duration_seconds
        ):
            logger.info(
                "function=run_discovery | crawl_limit_hit discovered=%s requests=%s elapsed=%.1fs",
                len(discovered), request_count, elapsed,
            )
            break

        url, depth = queue.popleft()
        if url in visited or depth > effective_max_depth:
            continue
        visited.add(url)

        parsed = urlparse(url)
        if is_blocked_by_robots(parsed.path or "/", robots.blocked_paths):
            logger.info("function=run_discovery | url_blocked url=%s depth=%s", url, depth)
            discovered.append(DiscoveredUrl(url=url, depth=depth, status=UrlStatus.blocked_by_robots))
            continue

        try:
            logger.info("function=run_discovery | fetching url=%s depth=%s", url, depth)
            response = await client.get(url)
            request_count += 1
            logger.info("function=run_discovery | fetched url=%s status_code=%s", url, response.status_code)
        except httpx.HTTPError as exc:
            logger.info("function=run_discovery | fetch_error url=%s error=%s", url, exc)
            discovered.append(DiscoveredUrl(url=url, depth=depth, status=UrlStatus.fetch_error))
            continue

        discovered.append(DiscoveredUrl(url=url, depth=depth, status=UrlStatus.allowed))

        if depth < effective_max_depth:
            soup = BeautifulSoup(response.text, "lxml")
            for tag in soup.find_all("a", href=True):
                absolute = urljoin(url, tag["href"])
                clean = urlparse(absolute)._replace(fragment="", query="").geturl()
                if is_same_domain(clean, root_url) and clean not in visited:
                    queue.append((clean, depth + 1))

        await asyncio.sleep(3)

    duration = round(time.monotonic() - start, 2)
    allowed = [u for u in discovered if u.status == UrlStatus.allowed]

    result = DiscoveryResult(
        root_url=root_url,
        robots_policy=robots,
        discovered_urls=discovered,
        total_discovered=len(discovered),
        total_allowed=len(allowed),
        hit_limit=len(discovered) >= effective_max_urls,
        duration_seconds=duration,
    )
    logger.info(
        "function=run_discovery | result=total_discovered=%s total_allowed=%s hit_limit=%s duration_seconds=%s",
        result.total_discovered, result.total_allowed, result.hit_limit, result.duration_seconds,
    )
    return result


async def stream_discovery(
    client: httpx.AsyncClient,
    root_url: str,
    max_urls: int | None = None,
    max_depth: int | None = None,
) -> AsyncGenerator[DiscoveryEvent, None]:
    """BFS crawl identical to run_discovery() but yields DiscoveryEvent progress events."""
    effective_max_urls = min(max_urls, settings.discovery_max_urls) if max_urls is not None else settings.discovery_max_urls
    effective_max_depth = min(max_depth, settings.discovery_max_depth) if max_depth is not None else settings.discovery_max_depth
    logger.info(
        "function=stream_discovery | url=%s max_urls=%s max_depth=%s",
        root_url, effective_max_urls, effective_max_depth,
    )
    start = time.monotonic()

    max_dur = settings.discovery_max_duration_seconds

    yield DiscoveryEvent(
        type=DiscoveryEventType.phase,
        message=f"Starting discovery for {root_url}",
        elapsed_seconds=0.0,
        max_duration_seconds=max_dur,
    )

    robots_url = urljoin(root_url, "/robots.txt")
    yield DiscoveryEvent(
        type=DiscoveryEventType.phase,
        message=f"Fetching robots.txt from {robots_url}",
        elapsed_seconds=round(time.monotonic() - start, 1),
        max_duration_seconds=max_dur,
    )
    robots = await fetch_robots_txt(client, root_url)

    if robots.fetched:
        robots_msg = f"robots.txt found — {len(robots.blocked_paths)} blocked path(s)"
        if robots.sitemap_urls:
            robots_msg += f", {len(robots.sitemap_urls)} sitemap(s)"
    else:
        robots_msg = "No robots.txt found — all paths allowed"
    yield DiscoveryEvent(
        type=DiscoveryEventType.phase,
        message=robots_msg,
        elapsed_seconds=round(time.monotonic() - start, 1),
        max_duration_seconds=max_dur,
    )

    discovered: list[DiscoveredUrl] = []
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(root_url, 0)])
    request_count = 0

    while queue:
        elapsed = time.monotonic() - start
        if (
            len(discovered) >= effective_max_urls
            or request_count >= settings.discovery_max_requests
            or elapsed > settings.discovery_max_duration_seconds
        ):
            logger.info(
                "function=stream_discovery | crawl_limit_hit discovered=%s requests=%s elapsed=%.1fs",
                len(discovered), request_count, elapsed,
            )
            break

        url, depth = queue.popleft()
        if url in visited or depth > effective_max_depth:
            continue
        visited.add(url)

        parsed = urlparse(url)
        if is_blocked_by_robots(parsed.path or "/", robots.blocked_paths):
            logger.info("function=stream_discovery | url_blocked url=%s depth=%s", url, depth)
            discovered.append(DiscoveredUrl(url=url, depth=depth, status=UrlStatus.blocked_by_robots))
            yield DiscoveryEvent(
                type=DiscoveryEventType.url,
                message=f"Blocked by robots.txt: {url}",
                count=len(discovered),
                elapsed_seconds=round(time.monotonic() - start, 1),
                max_duration_seconds=max_dur,
            )
            continue

        try:
            logger.info("function=stream_discovery | fetching url=%s depth=%s", url, depth)
            yield DiscoveryEvent(
                type=DiscoveryEventType.url,
                message=f"Crawling {url}",
                count=len(discovered) + 1,
                elapsed_seconds=round(time.monotonic() - start, 1),
                max_duration_seconds=max_dur,
            )
            response = await client.get(url)
            request_count += 1
            logger.info("function=stream_discovery | fetched url=%s status_code=%s", url, response.status_code)
        except httpx.HTTPError as exc:
            logger.info("function=stream_discovery | fetch_error url=%s error=%s", url, exc)
            discovered.append(DiscoveredUrl(url=url, depth=depth, status=UrlStatus.fetch_error))
            yield DiscoveryEvent(
                type=DiscoveryEventType.url,
                message=f"Failed to fetch: {url}",
                count=len(discovered),
                elapsed_seconds=round(time.monotonic() - start, 1),
                max_duration_seconds=max_dur,
            )
            continue

        discovered.append(DiscoveredUrl(url=url, depth=depth, status=UrlStatus.allowed))

        if depth < effective_max_depth:
            soup = BeautifulSoup(response.text, "lxml")
            for tag in soup.find_all("a", href=True):
                absolute = urljoin(url, tag["href"])
                clean = urlparse(absolute)._replace(fragment="", query="").geturl()
                if is_same_domain(clean, root_url) and clean not in visited:
                    queue.append((clean, depth + 1))

        await asyncio.sleep(3)

    duration = round(time.monotonic() - start, 2)
    allowed = [u for u in discovered if u.status == UrlStatus.allowed]

    result = DiscoveryResult(
        root_url=root_url,
        robots_policy=robots,
        discovered_urls=discovered,
        total_discovered=len(discovered),
        total_allowed=len(allowed),
        hit_limit=len(discovered) >= effective_max_urls,
        duration_seconds=duration,
    )
    logger.info(
        "function=stream_discovery | result=total_discovered=%s total_allowed=%s hit_limit=%s duration_seconds=%s",
        result.total_discovered, result.total_allowed, result.hit_limit, result.duration_seconds,
    )
    yield DiscoveryEvent(type=DiscoveryEventType.complete, message="Discovery complete", result=result)
