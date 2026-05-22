from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class CategoryStatus(str, Enum):
    ok = "ok"
    error = "error"
    not_included = "not_included"


class CategoryResult(BaseModel):
    name: str
    score: int | None           # 0-100; None when status != ok
    status: CategoryStatus
    error: str | None = None    # human-readable reason, set only when status=error


class ScoreBreakdown(BaseModel):
    categories: list[CategoryResult]
    overall_score: int | None   # simple average of ok categories; None if none ok
    grade: str | None           # None if no ok categories
