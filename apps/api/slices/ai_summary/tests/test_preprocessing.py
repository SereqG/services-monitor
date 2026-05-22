from __future__ import annotations

from slices.ai_summary.preprocessing import (
    build_ai_dataset,
    consistency_score,
    rank_problematic_pages,
)
from slices.ai_summary.tests import _builders as b


def test_consistency_stable_scores_is_high():
    assert consistency_score([68, 71, 69, 72]) == 98


def test_consistency_volatile_scores_is_low():
    assert consistency_score([10, 100, 20, 90]) == 60


def test_consistency_empty_or_single_is_full():
    assert consistency_score([]) == 100
    assert consistency_score([50]) == 100


def test_consistency_stays_within_bounds():
    assert 0 <= consistency_score([0, 0, 100, 100]) <= 100


def test_problematic_pages_sorted_worst_first():
    pages = [
        b.page("https://example.com/a", seo_score=40),
        b.page("https://example.com/b", seo_score=60),
        b.page("https://example.com/c", seo_score=90),
    ]
    ranked = rank_problematic_pages(pages, global_seo_avg=70.0, global_accessibility_avg=0.0)
    assert [p.url for p in ranked] == ["https://example.com/a", "https://example.com/b"]
    assert ranked[0].weakness_score == 30
    assert ranked[1].weakness_score == 10


def test_problematic_pages_excludes_pages_at_or_above_average():
    pages = [b.page("https://example.com/strong", seo_score=95)]
    ranked = rank_problematic_pages(pages, global_seo_avg=70.0, global_accessibility_avg=0.0)
    assert ranked == []


def test_problematic_pages_url_tiebreak_is_ascending():
    pages = [
        b.page("https://example.com/z", seo_score=40),
        b.page("https://example.com/a", seo_score=40),
    ]
    ranked = rank_problematic_pages(pages, global_seo_avg=60.0, global_accessibility_avg=0.0)
    assert [p.url for p in ranked] == ["https://example.com/a", "https://example.com/z"]


def test_problematic_pages_capped_at_limit():
    pages = [b.page(f"https://example.com/p{i:02d}", seo_score=10) for i in range(15)]
    ranked = rank_problematic_pages(pages, global_seo_avg=80.0, global_accessibility_avg=0.0)
    assert len(ranked) == 10


def test_problematic_pages_missing_seo_uses_accessibility_only():
    pages = [b.page("https://example.com/a", accessibility_score=50)]
    ranked = rank_problematic_pages(pages, global_seo_avg=90.0, global_accessibility_avg=70.0)
    assert len(ranked) == 1
    assert ranked[0].weakness_score == 20
    assert ranked[0].seo_score is None


def test_build_dataset_is_deterministic():
    pages = [
        b.page("https://example.com/", seo_score=80, accessibility_score=70,
                page_health=b.health()),
        b.page("https://example.com/a", seo_score=40, accessibility_score=55,
                page_health=b.health()),
    ]
    report = b.report(pages)
    first = build_ai_dataset(report, "a" * 32)
    second = build_ai_dataset(report, "a" * 32)
    assert first.model_dump() == second.model_dump()


def test_build_dataset_copies_overall_score_and_grade():
    report = b.report([b.page("https://example.com/", seo_score=72)], overall_score=72, grade="C")
    dataset = build_ai_dataset(report, "b" * 32)
    assert dataset.general_info.overall_score == 72
    assert dataset.general_info.grade == "C"
    assert dataset.audit_id == "b" * 32


def test_build_dataset_aggregates_categories():
    pages = [
        b.page("https://example.com/", seo_score=80, accessibility_score=60,
                page_health=b.health()),
        b.page("https://example.com/a", seo_score=40, accessibility_score=60,
                page_health=b.health(is_available=False)),
    ]
    dataset = build_ai_dataset(b.report(pages), "c" * 32)
    categories = dataset.general_info.categories
    assert categories["seo"].average_score == 60
    assert categories["accessibility"].average_score == 60
    assert categories["accessibility"].consistency == 100  # identical scores
    assert categories["health"].average_score == 50


def test_build_dataset_common_issues_ranked_by_frequency():
    common = b.seo_issue("Missing meta description")
    rare = b.seo_issue("Multiple H1 headings")
    pages = [
        b.page("https://example.com/", seo_score=50, seo_issues=[common, rare]),
        b.page("https://example.com/a", seo_score=50, seo_issues=[common]),
        b.page("https://example.com/b", seo_score=50, seo_issues=[common]),
    ]
    dataset = build_ai_dataset(b.report(pages), "d" * 32)
    assert dataset.general_info.categories["seo"].common_issues[0] == "Missing meta description"


def test_build_dataset_priority_areas_lists_weak_categories():
    pages = [b.page("https://example.com/", seo_score=30, accessibility_score=95)]
    dataset = build_ai_dataset(b.report(pages), "e" * 32)
    assert "seo" in dataset.general_info.priority_areas
    assert "accessibility" not in dataset.general_info.priority_areas
