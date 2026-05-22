from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.config import settings
from core.dependencies import get_http_client
from core.logging import logger
from slices.audit import service
from slices.audit.schemas import AuditRequest, AuditResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("", response_model=AuditResponse)
async def run_audit(
    body: AuditRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
) -> AuditResponse:
    logger.info("endpoint=POST /api/v1/audit | function=run_audit | url=%s", body.url)
    try:
        report = await asyncio.wait_for(
            service.run_audit(client, body),
            timeout=settings.audit_max_duration_seconds,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "endpoint=POST /api/v1/audit | result=timeout | url=%s limit_seconds=%s",
            body.url, settings.audit_max_duration_seconds,
        )
        raise HTTPException(
            status_code=504,
            detail=f"Audit exceeded the {settings.audit_max_duration_seconds}s time limit.",
        )
    logger.info(
        "endpoint=POST /api/v1/audit | function=run_audit | result=score=%s grade=%s pages=%s",
        report.score_breakdown.overall_score, report.score_breakdown.grade, report.discovery.total_discovered,
    )
    return AuditResponse(success=True, report=report)


@router.post("/stream")
async def run_audit_stream(
    body: AuditRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
) -> StreamingResponse:
    logger.info("endpoint=POST /api/v1/audit/stream | function=run_audit_stream | url=%s", body.url)

    async def event_stream() -> AsyncGenerator[str, None]:
        async for event in service.stream_audit(client, body):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
