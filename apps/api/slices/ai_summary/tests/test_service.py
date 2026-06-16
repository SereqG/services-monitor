from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.config import settings
from core.exceptions import AiSummaryError
from slices.ai_summary.providers import LLMCredentials
from slices.ai_summary.schemas import AiSummaryStatus
from slices.ai_summary.service import generate_ai_summary, safe_generate_ai_summary
from slices.ai_summary.storage import dataset_path
from slices.ai_summary.tests import _builders as b

AUDIT_ID = "a" * 32
_CREDS = LLMCredentials(provider="openrouter", api_key="test-key")

_PHASE1 = {
    "overall_assessment": "The website is in decent shape.",
    "main_strengths": ["fast pages"],
    "main_weaknesses": ["weak SEO"],
    "priority_recommendations": ["add meta descriptions"],
}
_PHASE2 = {
    "problematic_pages": [
        {
            "url": "https://example.com/weak",
            "summary": "This page has weak SEO and accessibility.",
            "recommended_actions": ["add headings"],
        }
    ]
}


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ai_storage_dir", str(tmp_path))


def _multi_page_report():
    return b.report(
        [
            b.page("https://example.com/", seo_score=85, accessibility_score=80,
                    page_health=b.health()),
            b.page("https://example.com/weak", seo_score=20, accessibility_score=25,
                    page_health=b.health()),
        ]
    )


def _single_page_report():
    return b.report(
        [b.page("https://example.com/", seo_score=85, accessibility_score=80,
                 page_health=b.health())]
    )


async def test_generate_ai_summary_happy_path():
    completion = AsyncMock(side_effect=[_PHASE1, _PHASE2])
    with patch("slices.ai_summary.service.run_completion", completion):
        summary = await generate_ai_summary(
            MagicMock(), _multi_page_report(), AUDIT_ID, _CREDS
        )

    assert summary.status == AiSummaryStatus.ok
    assert summary.summary is not None
    assert summary.summary.overall_assessment == "The website is in decent shape."
    assert len(summary.problematic_pages) == 1
    assert summary.problematic_pages[0].url == "https://example.com/weak"
    assert completion.await_count == 2
    # The model recorded on the summary comes from the chosen provider.
    assert summary.model == "google/gemini-2.5-flash"


async def test_generate_ai_summary_writes_dataset():
    completion = AsyncMock(side_effect=[_PHASE1, _PHASE2])
    with patch("slices.ai_summary.service.run_completion", completion):
        await generate_ai_summary(MagicMock(), _multi_page_report(), AUDIT_ID, _CREDS)
    assert dataset_path(AUDIT_ID).exists()


async def test_generate_ai_summary_skips_phase2_when_no_weak_pages():
    completion = AsyncMock(side_effect=[_PHASE1])
    with patch("slices.ai_summary.service.run_completion", completion):
        summary = await generate_ai_summary(
            MagicMock(), _single_page_report(), AUDIT_ID, _CREDS
        )

    assert summary.status == AiSummaryStatus.ok
    assert summary.problematic_pages == []
    assert completion.await_count == 1


async def test_safe_generate_swallows_ai_summary_error():
    completion = AsyncMock(side_effect=AiSummaryError("LLM unavailable", code="AI_REQUEST_FAILED"))
    with patch("slices.ai_summary.service.run_completion", completion):
        summary = await safe_generate_ai_summary(
            MagicMock(), _multi_page_report(), AUDIT_ID, _CREDS
        )

    assert summary.status == AiSummaryStatus.error
    assert "LLM unavailable" in (summary.error or "")
    assert summary.audit_id == AUDIT_ID


async def test_safe_generate_swallows_unexpected_error():
    completion = AsyncMock(side_effect=RuntimeError("boom"))
    with patch("slices.ai_summary.service.run_completion", completion):
        summary = await safe_generate_ai_summary(
            MagicMock(), _multi_page_report(), AUDIT_ID, _CREDS
        )

    assert summary.status == AiSummaryStatus.error
    assert summary.error is not None
