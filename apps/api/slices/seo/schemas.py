from __future__ import annotations

from pydantic import BaseModel


class MetaData(BaseModel):
    title: str | None
    title_length: int | None
    description: str | None
    description_length: int | None
    canonical: str | None
    robots_meta: str | None
    og_title: str | None
    og_description: str | None
    og_image: str | None


class HeadingStructure(BaseModel):
    h1_count: int
    h2_count: int
    h3_count: int
    h1_texts: list[str]


class SeoIssue(BaseModel):
    code: str
    severity: str  # critical | high | medium | low | info
    message: str  # English; deterministic source of truth
    # Structured values behind any interpolated message, so clients can render a
    # localized template without re-parsing `message`. Empty for static issues.
    params: dict[str, int | str] = {}
    detail: str | None = None


class SeoAnalysisResult(BaseModel):
    url: str
    meta: MetaData
    headings: HeadingStructure
    has_sitemap: bool
    has_schema_markup: bool
    images_without_alt: int
    issues: list[SeoIssue]
    score: int  # 0-100
