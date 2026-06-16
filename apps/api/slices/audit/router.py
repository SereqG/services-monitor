from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from core.config import settings
from core.dependencies import get_http_client
from core.logging import logger
from slices.ai_summary.providers import LLMCredentials
from slices.audit import service
from slices.audit.schemas import AuditRequest, AuditResponse

router = APIRouter(prefix="/audit", tags=["audit"])


def _build_credentials(
    request: AuditRequest, api_key: str | None
) -> LLMCredentials | None:
    """Combine the body's provider with the header's secret. None if incomplete.

    The key arrives only via the X-LLM-Api-Key header so it never lands in the
    request body, logs, or the persisted report.
    """
    if not request.enable_ai_summary:
        return None
    if request.llm_provider is None or not api_key:
        return None
    return LLMCredentials(provider=request.llm_provider, api_key=api_key)


@router.post("", response_model=AuditResponse)
async def run_audit(
    body: AuditRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
    x_llm_api_key: str | None = Header(default=None),
) -> AuditResponse:
    logger.info("endpoint=POST /api/v1/audit | function=run_audit | url=%s", body.url)
    credentials = _build_credentials(body, x_llm_api_key)
    try:
        report = await asyncio.wait_for(
            service.run_audit(client, body, credentials),
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
    x_llm_api_key: str | None = Header(default=None),
) -> StreamingResponse:
    logger.info("endpoint=POST /api/v1/audit/stream | function=run_audit_stream | url=%s", body.url)
    credentials = _build_credentials(body, x_llm_api_key)

    async def event_stream() -> AsyncGenerator[str, None]:
        async for event in service.stream_audit(client, body, credentials):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
