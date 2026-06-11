from __future__ import annotations

import pytest

from core.exceptions import AiSummaryError
from slices.ai_summary.schemas import AiSummaryOverview, AiSummaryStatus
from slices.ai_summary.transformers import (
    build_error_summary,
    build_success_summary,
    parse_overview,
    parse_problematic_pages,
)


def test_parse_overview_valid_payload():
    overview = parse_overview(
        {
            "overall_assessment": "The site is healthy.",
            "main_strengths": ["fast"],
            "main_weaknesses": ["weak seo"],
            "priority_recommendations": ["add meta descriptions"],
        }
    )
    assert overview.overall_assessment == "The site is healthy."
    assert overview.main_strengths == ["fast"]


def test_parse_overview_missing_required_field_raises():
    with pytest.raises(AiSummaryError):
        parse_overview({"main_strengths": ["fast"]})


def test_parse_problematic_pages_valid_payload():
    pages = parse_problematic_pages(
        {
            "problematic_pages": [
                {
                    "url": "https://example.com/a",
                    "summary": "This page is weak.",
                    "recommended_actions": ["fix headings"],
                }
            ]
        }
    )
    assert len(pages) == 1
    assert pages[0].url == "https://example.com/a"


def test_parse_problematic_pages_missing_key_returns_empty():
    assert parse_problematic_pages({}) == []


def test_parse_problematic_pages_non_list_raises():
    with pytest.raises(AiSummaryError):
        parse_problematic_pages({"problematic_pages": "not a list"})


def test_parse_problematic_pages_invalid_entry_raises():
    with pytest.raises(AiSummaryError):
        parse_problematic_pages({"problematic_pages": [{"summary": "no url here"}]})


def test_build_success_summary():
    overview = AiSummaryOverview(overall_assessment="All good")
    summary = build_success_summary("a" * 32, overview, [])
    assert summary.status == AiSummaryStatus.ok
    assert summary.summary is not None
    assert summary.summary.overall_assessment == "All good"
    assert summary.error is None
    assert summary.generated_at is not None
    assert summary.language == "en"  # default preserves prior behavior


def test_build_success_summary_records_language():
    overview = AiSummaryOverview(overall_assessment="Wszystko w porządku")
    summary = build_success_summary("a" * 32, overview, [], "pl")
    assert summary.language == "pl"


def test_build_error_summary():
    summary = build_error_summary("a" * 32, "Something failed")
    assert summary.status == AiSummaryStatus.error
    assert summary.error == "Something failed"
    assert summary.summary is None
    assert summary.language == "en"


def test_build_error_summary_records_language():
    summary = build_error_summary("a" * 32, "Coś poszło nie tak", "pl")
    assert summary.language == "pl"
