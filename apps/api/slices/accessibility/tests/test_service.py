from __future__ import annotations

from bs4 import BeautifulSoup

from slices.accessibility.service import calculate_accessibility_score, run_heuristic_checks
from slices.accessibility.schemas import AccessibilityIssue


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def test_detects_img_without_alt():
    soup = _soup('<html><body><img src="x.jpg"/></body></html>')
    issues = run_heuristic_checks(soup)
    assert any(i.code == "IMG_MISSING_ALT" for i in issues)


def test_img_with_alt_passes():
    soup = _soup('<html><body><img src="x.jpg" alt="description"/></body></html>')
    issues = run_heuristic_checks(soup)
    assert not any(i.code == "IMG_MISSING_ALT" for i in issues)


def test_detects_missing_main_landmark():
    soup = _soup("<html><body><p>content</p></body></html>")
    issues = run_heuristic_checks(soup)
    assert any(i.code == "MISSING_MAIN_LANDMARK" for i in issues)


def test_main_tag_satisfies_landmark():
    soup = _soup("<html><body><main><p>content</p></main></body></html>")
    issues = run_heuristic_checks(soup)
    assert not any(i.code == "MISSING_MAIN_LANDMARK" for i in issues)


def test_role_main_satisfies_landmark():
    soup = _soup('<html><body><div role="main">content</div></body></html>')
    issues = run_heuristic_checks(soup)
    assert not any(i.code == "MISSING_MAIN_LANDMARK" for i in issues)


def test_detects_missing_lang():
    soup = _soup("<html><body></body></html>")
    issues = run_heuristic_checks(soup)
    assert any(i.code == "MISSING_LANG_ATTR" for i in issues)


def test_lang_present_passes():
    soup = _soup('<html lang="en"><body></body></html>')
    issues = run_heuristic_checks(soup)
    assert not any(i.code == "MISSING_LANG_ATTR" for i in issues)


def test_score_deduction():
    issues = [AccessibilityIssue(code="X", severity="serious", message="x")]
    assert calculate_accessibility_score(issues) == 85


def test_score_floor_is_zero():
    issues = [AccessibilityIssue(code=f"X{i}", severity="critical", message="x") for i in range(10)]
    assert calculate_accessibility_score(issues) == 0
