from __future__ import annotations

from pydantic import BaseModel


class AccessibilityIssue(BaseModel):
    code: str
    severity: str  # critical | serious | moderate | minor
    message: str
    element: str | None = None
    count: int = 1


class AccessibilityResult(BaseModel):
    url: str
    issues: list[AccessibilityIssue]
    score: int  # 0-100
    checked_with: str
    note: str | None = None
