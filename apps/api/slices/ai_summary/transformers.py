from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from core.config import settings
from core.exceptions import AiSummaryError
from slices.ai_summary.schemas import (
    AiPageSummary,
    AiSummary,
    AiSummaryOverview,
    AiSummaryStatus,
)


def parse_overview(payload: dict[str, Any]) -> AiSummaryOverview:
    """Validate the completion-1 JSON payload into a strict overview model."""
    try:
        return AiSummaryOverview.model_validate(payload)
    except ValidationError as exc:
        raise AiSummaryError(
            f"AI overall summary did not match the expected schema: {exc}",
            code="AI_BAD_OVERVIEW",
        ) from exc


def parse_problematic_pages(payload: dict[str, Any]) -> list[AiPageSummary]:
    """Validate the completion-2 JSON payload into per-page summary models."""
    raw_pages = payload.get("problematic_pages", [])
    if not isinstance(raw_pages, list):
        raise AiSummaryError(
            "AI weak-pages response did not contain a 'problematic_pages' list.",
            code="AI_BAD_PAGES",
        )
    try:
        return [AiPageSummary.model_validate(item) for item in raw_pages]
    except ValidationError as exc:
        raise AiSummaryError(
            f"AI weak-page entry did not match the expected schema: {exc}",
            code="AI_BAD_PAGES",
        ) from exc


def build_success_summary(
    audit_id: str,
    overview: AiSummaryOverview,
    pages: list[AiPageSummary],
    language: str = "en",
) -> AiSummary:
    return AiSummary(
        status=AiSummaryStatus.ok,
        audit_id=audit_id,
        model=settings.ai_summary_model,
        language=language,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        summary=overview,
        problematic_pages=pages,
    )


def build_error_summary(audit_id: str, error: str, language: str = "en") -> AiSummary:
    return AiSummary(
        status=AiSummaryStatus.error,
        audit_id=audit_id,
        model=settings.ai_summary_model,
        language=language,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        error=error,
    )
