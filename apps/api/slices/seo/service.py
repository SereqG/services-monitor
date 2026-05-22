from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from core.logging import logger
from slices.seo.schemas import HeadingStructure, MetaData, SeoAnalysisResult, SeoIssue

_TITLE_MIN = 30
_TITLE_MAX = 60
_DESC_MIN = 120
_DESC_MAX = 160

_SEVERITY_DEDUCTIONS = {"critical": 25, "high": 15, "medium": 8, "low": 3, "info": 0}


def extract_meta(soup: BeautifulSoup) -> MetaData:
    logger.info("function=extract_meta")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    def _meta_content(name: str | None = None, prop: str | None = None) -> str | None:
        tag = (
            soup.find("meta", attrs={"name": name})
            if name
            else soup.find("meta", attrs={"property": prop})
        )
        return tag.get("content") if tag else None

    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag.get("href") if canonical_tag else None

    description = _meta_content(name="description")

    result = MetaData(
        title=title,
        title_length=len(title) if title else None,
        description=description,
        description_length=len(description) if description else None,
        canonical=canonical,
        robots_meta=_meta_content(name="robots"),
        og_title=_meta_content(prop="og:title"),
        og_description=_meta_content(prop="og:description"),
        og_image=_meta_content(prop="og:image"),
    )
    logger.info(
        "function=extract_meta | result=title=%r title_length=%s description_length=%s canonical=%s",
        result.title, result.title_length, result.description_length, result.canonical,
    )
    return result


def extract_headings(soup: BeautifulSoup) -> HeadingStructure:
    logger.info("function=extract_headings")
    h1s = soup.find_all("h1")
    result = HeadingStructure(
        h1_count=len(h1s),
        h2_count=len(soup.find_all("h2")),
        h3_count=len(soup.find_all("h3")),
        h1_texts=[h.get_text(strip=True) for h in h1s],
    )
    logger.info(
        "function=extract_headings | result=h1=%s h2=%s h3=%s",
        result.h1_count, result.h2_count, result.h3_count,
    )
    return result


def collect_issues(meta: MetaData, headings: HeadingStructure) -> list[SeoIssue]:
    logger.info("function=collect_issues")
    issues: list[SeoIssue] = []

    if not meta.title:
        issues.append(SeoIssue(code="MISSING_TITLE", severity="critical", message="Page title is missing"))
    elif meta.title_length and meta.title_length < _TITLE_MIN:
        issues.append(SeoIssue(code="TITLE_TOO_SHORT", severity="medium", message=f"Title too short ({meta.title_length} chars, min {_TITLE_MIN})"))
    elif meta.title_length and meta.title_length > _TITLE_MAX:
        issues.append(SeoIssue(code="TITLE_TOO_LONG", severity="low", message=f"Title too long ({meta.title_length} chars, max {_TITLE_MAX})"))

    if not meta.description:
        issues.append(SeoIssue(code="MISSING_DESCRIPTION", severity="high", message="Meta description is missing"))
    elif meta.description_length and meta.description_length < _DESC_MIN:
        issues.append(SeoIssue(code="DESC_TOO_SHORT", severity="medium", message=f"Meta description too short ({meta.description_length} chars, min {_DESC_MIN})"))
    elif meta.description_length and meta.description_length > _DESC_MAX:
        issues.append(SeoIssue(code="DESC_TOO_LONG", severity="low", message=f"Meta description too long ({meta.description_length} chars, max {_DESC_MAX})"))

    if headings.h1_count == 0:
        issues.append(SeoIssue(code="MISSING_H1", severity="high", message="No H1 heading found"))
    elif headings.h1_count > 1:
        issues.append(SeoIssue(code="MULTIPLE_H1", severity="medium", message=f"Multiple H1 headings found ({headings.h1_count})"))

    if not meta.canonical:
        issues.append(SeoIssue(code="MISSING_CANONICAL", severity="medium", message="Canonical tag is missing"))

    logger.info(
        "function=collect_issues | result=issues=%s codes=%s",
        len(issues), [i.code for i in issues],
    )
    return issues


def calculate_seo_score(issues: list[SeoIssue]) -> int:
    logger.info("function=calculate_seo_score | issues=%s", len(issues))
    total_deduction = sum(_SEVERITY_DEDUCTIONS.get(i.severity, 0) for i in issues)
    score = max(0, 100 - total_deduction)
    logger.info("function=calculate_seo_score | result=score=%s total_deduction=%s", score, total_deduction)
    return score


async def analyze_seo(client: httpx.AsyncClient, url: str) -> SeoAnalysisResult:
    logger.info("function=analyze_seo | url=%s", url)
    response = await client.get(url)
    logger.info("function=analyze_seo | fetched status_code=%s content_length=%s", response.status_code, len(response.text))
    soup = BeautifulSoup(response.text, "lxml")

    meta = extract_meta(soup)
    headings = extract_headings(soup)
    issues = collect_issues(meta, headings)

    images_without_alt = len([img for img in soup.find_all("img") if not img.get("alt")])
    if images_without_alt > 0:
        issues.append(SeoIssue(
            code="IMAGES_MISSING_ALT",
            severity="medium",
            message=f"{images_without_alt} image(s) missing alt attribute",
        ))

    has_schema = bool(soup.find("script", type="application/ld+json"))
    score = calculate_seo_score(issues)

    result = SeoAnalysisResult(
        url=url,
        meta=meta,
        headings=headings,
        has_sitemap=False,  # resolved from discovery phase, not from HTML
        has_schema_markup=has_schema,
        images_without_alt=images_without_alt,
        issues=issues,
        score=score,
    )
    logger.info(
        "function=analyze_seo | result=score=%s issues=%s has_schema=%s images_without_alt=%s",
        result.score, len(result.issues), result.has_schema_markup, result.images_without_alt,
    )
    return result
