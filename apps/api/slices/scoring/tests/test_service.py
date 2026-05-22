from __future__ import annotations

from slices.scoring.schemas import CategoryResult, CategoryStatus
from slices.scoring.service import calculate_score, grade


def _ok(name: str, score: int) -> CategoryResult:
    return CategoryResult(name=name, score=score, status=CategoryStatus.ok)


def _error(name: str, msg: str) -> CategoryResult:
    return CategoryResult(name=name, score=None, status=CategoryStatus.error, error=msg)


def _not_included(name: str) -> CategoryResult:
    return CategoryResult(name=name, score=None, status=CategoryStatus.not_included)


def test_perfect_score_is_100_grade_a():
    categories = [_ok(n, 100) for n in ("health", "seo", "accessibility", "performance", "security")]
    result = calculate_score(categories)
    assert result.overall_score == 100
    assert result.grade == "A"


def test_zero_score_is_0_grade_f():
    categories = [_ok(n, 0) for n in ("health", "seo", "accessibility", "performance", "security")]
    result = calculate_score(categories)
    assert result.overall_score == 0
    assert result.grade == "F"


def test_overall_score_is_simple_average_of_ok_categories():
    categories = [_ok("seo", 80), _ok("health", 60)]
    result = calculate_score(categories)
    assert result.overall_score == 70


def test_error_categories_excluded_from_average():
    categories = [_ok("seo", 100), _error("performance", "TTFB unavailable")]
    result = calculate_score(categories)
    assert result.overall_score == 100


def test_not_included_categories_excluded_from_average():
    categories = [_ok("seo", 80), _not_included("security")]
    result = calculate_score(categories)
    assert result.overall_score == 80


def test_all_error_categories_gives_none_overall_score():
    categories = [_error("seo", "failed"), _error("health", "timeout")]
    result = calculate_score(categories)
    assert result.overall_score is None
    assert result.grade is None


def test_empty_categories_gives_none_overall_score():
    result = calculate_score([])
    assert result.overall_score is None
    assert result.grade is None


def test_grade_boundaries():
    assert grade(90) == "A"
    assert grade(89) == "B"
    assert grade(75) == "B"
    assert grade(74) == "C"
    assert grade(60) == "C"
    assert grade(59) == "D"
    assert grade(40) == "D"
    assert grade(39) == "F"
