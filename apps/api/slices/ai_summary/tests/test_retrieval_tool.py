from __future__ import annotations

import pytest

from core.config import settings
from slices.ai_summary.retrieval_tool import TOOL_NAME, TOOL_SPEC, run_audit_context_tool
from slices.ai_summary.schemas import (
    AiAnalysisDataset,
    CategorySummary,
    GeneralInfo,
    ProblematicPage,
)
from slices.ai_summary.storage import write_dataset

AUDIT_ID = "a" * 32
PAGE_URL = "https://example.com/weak"


@pytest.fixture(autouse=True)
def _dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ai_storage_dir", str(tmp_path))
    write_dataset(
        AiAnalysisDataset(
            audit_id=AUDIT_ID,
            root_url="https://example.com/",
            generated_at="2026-05-21T10:00:00+00:00",
            general_info=GeneralInfo(
                overall_score=64,
                grade="C",
                categories={"seo": CategorySummary(average_score=55, consistency=80)},
                priority_areas=["seo"],
                problematic_pages=[
                    ProblematicPage(url=PAGE_URL, weakness_score=25, seo_score=40),
                ],
            ),
        )
    )


def test_tool_spec_exposes_expected_name_and_modes():
    assert TOOL_SPEC["function"]["name"] == TOOL_NAME
    assert TOOL_SPEC["function"]["parameters"]["properties"]["mode"]["enum"] == [
        "general_info",
        "per_page_info",
    ]


def test_general_info_returns_curated_section():
    result = run_audit_context_tool(AUDIT_ID, "general_info")
    assert result["overall_score"] == 64
    assert result["grade"] == "C"
    assert "seo" in result["categories"]
    assert "error" not in result


def test_per_page_info_returns_matching_page():
    result = run_audit_context_tool(AUDIT_ID, "per_page_info", url=PAGE_URL)
    assert result["url"] == PAGE_URL
    assert result["weakness_score"] == 25


def test_per_page_info_unknown_url_returns_error_dict():
    result = run_audit_context_tool(AUDIT_ID, "per_page_info", url="https://example.com/missing")
    assert "error" in result


def test_per_page_info_without_url_returns_error_dict():
    result = run_audit_context_tool(AUDIT_ID, "per_page_info")
    assert "error" in result


def test_unknown_mode_returns_error_dict():
    result = run_audit_context_tool(AUDIT_ID, "everything")
    assert "error" in result


def test_missing_dataset_returns_error_dict_without_raising():
    result = run_audit_context_tool("f" * 32, "general_info")
    assert "error" in result
