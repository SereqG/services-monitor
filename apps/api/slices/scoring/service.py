from __future__ import annotations

from core.logging import logger
from slices.scoring.schemas import CategoryResult, CategoryStatus, ScoreBreakdown


def grade(score: int) -> str:
    logger.info("function=grade | score=%s", score)
    if score >= 90:
        result = "A"
    elif score >= 75:
        result = "B"
    elif score >= 60:
        result = "C"
    elif score >= 40:
        result = "D"
    else:
        result = "F"
    logger.info("function=grade | result=%s", result)
    return result


def calculate_score(categories: list[CategoryResult]) -> ScoreBreakdown:
    """
    Produces a transparent, auditable score as a simple average of ok categories.
    Categories with status=error or status=not_included are excluded from the average.
    """
    logger.info(
        "function=calculate_score | categories=%s",
        [(c.name, c.status, c.score) for c in categories],
    )

    ok_scores = [c.score for c in categories if c.status == CategoryStatus.ok and c.score is not None]
    overall: int | None = round(sum(ok_scores) / len(ok_scores)) if ok_scores else None
    result_grade: str | None = grade(overall) if overall is not None else None

    logger.info(
        "function=calculate_score | result=overall_score=%s grade=%s ok_count=%s",
        overall, result_grade, len(ok_scores),
    )
    return ScoreBreakdown(categories=categories, overall_score=overall, grade=result_grade)
