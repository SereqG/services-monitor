from __future__ import annotations

from typing import AsyncGenerator

import httpx

from core.http_client import create_http_client


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with create_http_client() as client:
        yield client
