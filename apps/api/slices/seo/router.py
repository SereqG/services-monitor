from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.dependencies import get_http_client
from core.logging import logger
from slices.seo import service
from slices.seo.schemas import SeoAnalysisResult

router = APIRouter(prefix="/seo", tags=["seo"])


class SeoRequest(BaseModel):
    url: str


@router.post("", response_model=SeoAnalysisResult)
async def analyze_seo(
    body: SeoRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
) -> SeoAnalysisResult:
    logger.info("endpoint=POST /api/v1/seo | function=analyze_seo | url=%s", body.url)
    result = await service.analyze_seo(client, body.url)
    logger.info(
        "endpoint=POST /api/v1/seo | function=analyze_seo | result=score=%s issues=%s",
        result.score, len(result.issues),
    )
    return result
