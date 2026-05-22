from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from core.logging import logger
from slices.accessibility.schemas import AccessibilityIssue, AccessibilityResult

_SEVERITY_DEDUCTIONS = {"critical": 25, "serious": 15, "moderate": 8, "minor": 3}


def run_heuristic_checks(soup: BeautifulSoup) -> list[AccessibilityIssue]:
    """HTML-level accessibility heuristics that do not require a browser."""
    logger.info("function=run_heuristic_checks")
    issues: list[AccessibilityIssue] = []

    imgs_no_alt = [img for img in soup.find_all("img") if not img.get("alt")]
    logger.info("function=run_heuristic_checks | check=IMG_MISSING_ALT count=%s", len(imgs_no_alt))
    if imgs_no_alt:
        issues.append(AccessibilityIssue(
            code="IMG_MISSING_ALT",
            severity="serious",
            message="Images missing alt attribute",
            count=len(imgs_no_alt),
        ))

    inputs = soup.find_all(
        "input",
        type=lambda t: t not in ("hidden", "submit", "button", "image"),
    )
    unlabeled = [i for i in inputs if not i.get("aria-label") and not i.get("id")]
    logger.info("function=run_heuristic_checks | check=INPUT_MISSING_LABEL unlabeled=%s total_inputs=%s", len(unlabeled), len(inputs))
    if unlabeled:
        issues.append(AccessibilityIssue(
            code="INPUT_MISSING_LABEL",
            severity="serious",
            message="Form inputs without labels or aria-label",
            count=len(unlabeled),
        ))

    has_main = bool(soup.find("main") or soup.find(attrs={"role": "main"}))
    logger.info("function=run_heuristic_checks | check=MISSING_MAIN_LANDMARK has_main=%s", has_main)
    if not has_main:
        issues.append(AccessibilityIssue(
            code="MISSING_MAIN_LANDMARK",
            severity="moderate",
            message="No <main> landmark found",
        ))

    html_tag = soup.find("html")
    has_lang = bool(html_tag and html_tag.get("lang"))
    logger.info("function=run_heuristic_checks | check=MISSING_LANG_ATTR has_lang=%s", has_lang)
    if html_tag and not has_lang:
        issues.append(AccessibilityIssue(
            code="MISSING_LANG_ATTR",
            severity="serious",
            message="<html> element is missing lang attribute",
        ))

    logger.info(
        "function=run_heuristic_checks | result=issues=%s codes=%s",
        len(issues), [i.code for i in issues],
    )
    return issues


def calculate_accessibility_score(issues: list[AccessibilityIssue]) -> int:
    logger.info("function=calculate_accessibility_score | issues=%s", len(issues))
    total_deduction = sum(_SEVERITY_DEDUCTIONS.get(i.severity, 0) for i in issues)
    score = max(0, 100 - total_deduction)
    logger.info("function=calculate_accessibility_score | result=score=%s total_deduction=%s", score, total_deduction)
    return score


async def analyze_accessibility(client: httpx.AsyncClient, url: str) -> AccessibilityResult:
    logger.info("function=analyze_accessibility | url=%s", url)
    response = await client.get(url)
    logger.info("function=analyze_accessibility | fetched status_code=%s content_length=%s", response.status_code, len(response.text))
    soup = BeautifulSoup(response.text, "lxml")
    issues = run_heuristic_checks(soup)
    score = calculate_accessibility_score(issues)

    result = AccessibilityResult(
        url=url,
        issues=issues,
        score=score,
        checked_with="html-heuristics",
        note="Full audit requires browser-based axe-core integration (Phase 2)",
    )
    logger.info(
        "function=analyze_accessibility | result=score=%s issues=%s",
        result.score, len(result.issues),
    )
    return result
