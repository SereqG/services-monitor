from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CategorySummary(BaseModel):
    """Deterministic per-category aggregate fed to the LLM as curated context."""

    average_score: int
    consistency: int  # 0-100; higher means scores are stable across pages
    common_issues: list[str] = []


class ProblematicPage(BaseModel):
    """A weak page selected by the deterministic problematic-pages algorithm."""

    url: str
    weakness_score: int
    seo_score: int | None = None
    accessibility_score: int | None = None
    health_available: bool | None = None
    top_issues: list[str] = []


class GeneralInfo(BaseModel):
    overall_score: int | None = None
    grade: str | None = None
    categories: dict[str, CategorySummary] = {}
    priority_areas: list[str] = []
    problematic_pages: list[ProblematicPage] = []


class AiAnalysisDataset(BaseModel):
    """Curated, deterministic dataset persisted per audit and read by the LLM tool.

    This is NEVER the raw AuditReport — only aggregated, noise-reduced context.
    """

    version: str = "1.0"
    audit_id: str
    root_url: str
    generated_at: str
    general_info: GeneralInfo


class AiSummaryStatus(str, Enum):
    ok = "ok"
    error = "error"


class AiSummaryOverview(BaseModel):
    overall_assessment: str
    main_strengths: list[str] = []
    main_weaknesses: list[str] = []
    priority_recommendations: list[str] = []


class AiPageSummary(BaseModel):
    url: str
    summary: str
    recommended_actions: list[str] = []


class AiSummary(BaseModel):
    """AI explanation layer attached to AuditReport. Optional and non-critical:
    `status=error` with an explicit `error` message when generation fails."""

    status: AiSummaryStatus
    audit_id: str
    model: str | None = None
    language: str = "en"  # language the prose was generated in; for traceability
    generated_at: str | None = None
    summary: AiSummaryOverview | None = None
    problematic_pages: list[AiPageSummary] = Field(default_factory=list)
    error: str | None = None
