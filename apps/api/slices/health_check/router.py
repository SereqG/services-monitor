from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.dependencies import get_http_client
from core.logging import logger
from slices.health_check import service
from slices.health_check.schemas import HealthCheckResult

router = APIRouter(prefix="/health-check", tags=["health-check"])


class HealthCheckRequest(BaseModel):
    url: str


@router.post("", response_model=HealthCheckResult)
async def run_health_check(
    body: HealthCheckRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
) -> HealthCheckResult:
    logger.info("endpoint=POST /api/v1/health-check | function=run_health_check | url=%s", body.url)
    result = await service.check_health(client, body.url)
    logger.info(
        "endpoint=POST /api/v1/health-check | function=run_health_check | result=status=%s status_code=%s is_available=%s ttfb_ms=%s",
        result.status, result.status_code, result.is_available, result.ttfb_ms,
    )
    return result
