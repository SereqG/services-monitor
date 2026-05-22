from __future__ import annotations

import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
import truststore

from core.config import settings


@asynccontextmanager
async def create_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    headers = {"User-Agent": settings.user_agent}
    ssl_ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    async with httpx.AsyncClient(
        headers=headers,
        timeout=settings.http_timeout,
        max_redirects=settings.http_max_redirects,
        follow_redirects=True,
        verify=ssl_ctx,
    ) as client:
        yield client
