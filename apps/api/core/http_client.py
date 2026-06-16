from __future__ import annotations

import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import truststore

from core.config import settings
from core.ssrf import assert_host_allowed


class SsrfGuardTransport(httpx.AsyncHTTPTransport):
    """Validates every outbound request — and every redirect hop — against the
    SSRF policy before it is sent.

    httpx re-enters the transport for each redirect, so blocking here covers the
    initial fetch and all hops centrally, without touching individual slices.
    """

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host:
            await assert_host_allowed(host)
        return await super().handle_async_request(request)


@asynccontextmanager
async def create_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    headers = {"User-Agent": settings.user_agent}
    ssl_ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    transport = SsrfGuardTransport(verify=ssl_ctx)
    async with httpx.AsyncClient(
        headers=headers,
        timeout=settings.http_timeout,
        max_redirects=settings.http_max_redirects,
        follow_redirects=True,
        transport=transport,
    ) as client:
        yield client
