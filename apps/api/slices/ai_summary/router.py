from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from core.dependencies import get_http_client
from core.exceptions import AiSummaryError
from core.logging import logger
from slices.ai_summary.llm_client import validate_credentials
from slices.ai_summary.providers import PROVIDERS, LLMCredentials, LLMProvider

router = APIRouter(prefix="/ai", tags=["ai"])


class ValidateKeyRequest(BaseModel):
    provider: LLMProvider


class ValidateKeyResponse(BaseModel):
    ok: bool
    model: str
    error: str | None = None


@router.post("/validate-key", response_model=ValidateKeyResponse)
async def validate_key(
    body: ValidateKeyRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
    x_llm_api_key: str | None = Header(default=None),
) -> ValidateKeyResponse:
    """Make a tiny live call to confirm the user's key works for their provider.

    Returns ok=true/false (never raises on a bad key) so the frontend can show a
    clear result. The key is read only from the header and never logged.
    """
    logger.info("endpoint=POST /api/v1/ai/validate-key | provider=%s", body.provider)
    model = PROVIDERS[body.provider].model
    if not x_llm_api_key:
        raise HTTPException(status_code=400, detail="Missing X-LLM-Api-Key header.")

    credentials = LLMCredentials(provider=body.provider, api_key=x_llm_api_key)
    try:
        await validate_credentials(client, credentials)
    except AiSummaryError as exc:
        logger.info(
            "endpoint=POST /api/v1/ai/validate-key | provider=%s result=invalid code=%s",
            body.provider,
            exc.code,
        )
        return ValidateKeyResponse(ok=False, model=model, error=exc.message)
    except Exception as exc:
        logger.exception(
            "endpoint=POST /api/v1/ai/validate-key | provider=%s result=error",
            body.provider,
        )
        return ValidateKeyResponse(
            ok=False, model=model, error=f"Could not validate the key: {exc}"
        )

    logger.info(
        "endpoint=POST /api/v1/ai/validate-key | provider=%s result=ok", body.provider
    )
    return ValidateKeyResponse(ok=True, model=model)
