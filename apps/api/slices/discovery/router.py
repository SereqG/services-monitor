from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from core.dependencies import get_http_client
from core.logging import logger
from slices.discovery import service
from slices.discovery.schemas import DiscoveryRequest, DiscoveryResult

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("", response_model=DiscoveryResult)
async def discover(
    body: DiscoveryRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
) -> DiscoveryResult:
    logger.info(
        "endpoint=POST /api/v1/discovery | function=discover | url=%s max_sites=%s max_depth=%s",
        body.url, body.max_sites, body.max_depth,
    )
    result = await service.run_discovery(client, body.url, max_urls=body.max_sites, max_depth=body.max_depth)
    logger.info(
        "endpoint=POST /api/v1/discovery | function=discover | result=total_discovered=%s total_allowed=%s duration_seconds=%s",
        result.total_discovered, result.total_allowed, result.duration_seconds,
    )
    return result


@router.post("/stream")
async def discover_stream(
    body: DiscoveryRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
) -> StreamingResponse:
    logger.info(
        "endpoint=POST /api/v1/discovery/stream | function=discover_stream | url=%s max_sites=%s max_depth=%s",
        body.url, body.max_sites, body.max_depth,
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        async for event in service.stream_discovery(client, body.url, max_urls=body.max_sites, max_depth=body.max_depth):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
