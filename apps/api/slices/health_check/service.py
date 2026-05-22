from __future__ import annotations

import time

import httpx

from core.logging import logger
from slices.health_check.schemas import HealthCheckResult, HttpStatus, RedirectHop


def classify_http_status(status_code: int) -> HttpStatus:
    if status_code < 300:
        return HttpStatus.ok
    if status_code < 400:
        return HttpStatus.redirect
    if status_code < 500:
        return HttpStatus.client_error
    return HttpStatus.server_error


async def check_health(client: httpx.AsyncClient, url: str) -> HealthCheckResult:
    logger.info("function=check_health | url=%s", url)
    redirect_chain: list[RedirectHop] = []
    seen_urls: set[str] = set()

    try:
        start = time.monotonic()
        response = await client.get(url)
        ttfb_ms = round((time.monotonic() - start) * 1000, 1)

        for r in response.history:
            seen_urls.add(str(r.url))
            redirect_chain.append(RedirectHop(url=str(r.url), status_code=r.status_code))

        final_url = str(response.url)
        has_redirect_loop = final_url in seen_urls

        result = HealthCheckResult(
            url=url,
            final_url=final_url,
            status_code=response.status_code,
            status=classify_http_status(response.status_code),
            ttfb_ms=ttfb_ms,
            redirect_chain=redirect_chain,
            has_redirect_loop=has_redirect_loop,
            is_available=response.status_code < 400,
        )
        logger.info(
            "function=check_health | result=status=%s status_code=%s is_available=%s ttfb_ms=%s redirects=%s",
            result.status, result.status_code, result.is_available, result.ttfb_ms, len(redirect_chain),
        )
        return result

    except httpx.TimeoutException:
        result = HealthCheckResult(
            url=url,
            final_url=url,
            status_code=None,
            status=HttpStatus.timeout,
            ttfb_ms=None,
            redirect_chain=redirect_chain,
            has_redirect_loop=False,
            is_available=False,
            error="Request timed out",
        )
        logger.info("function=check_health | result=status=timeout is_available=False error=Request timed out")
        return result
    except httpx.HTTPError as exc:
        result = HealthCheckResult(
            url=url,
            final_url=url,
            status_code=None,
            status=HttpStatus.connection_error,
            ttfb_ms=None,
            redirect_chain=redirect_chain,
            has_redirect_loop=False,
            is_available=False,
            error=str(exc),
        )
        logger.info("function=check_health | result=status=connection_error is_available=False error=%s", exc)
        return result
