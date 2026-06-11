from __future__ import annotations

from bs4 import BeautifulSoup

from slices.seo.schemas import HeadingStructure, MetaData, SeoIssue
from slices.seo.service import calculate_seo_score, collect_issues, extract_headings, extract_meta


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def test_extract_title():
    soup = _soup("<html><head><title>Hello World Title Here</title></head></html>")
    meta = extract_meta(soup)
    assert meta.title == "Hello World Title Here"
    assert meta.title_length == 22


def test_missing_title_returns_none():
    soup = _soup("<html><head></head></html>")
    meta = extract_meta(soup)
    assert meta.title is None
    assert meta.title_length is None


def test_extracts_meta_description():
    html = '<html><head><meta name="description" content="A great site."/></head></html>'
    soup = _soup(html)
    meta = extract_meta(soup)
    assert meta.description == "A great site."


def test_extracts_og_tags():
    html = '<html><head><meta property="og:title" content="OG Title"/></head></html>'
    soup = _soup(html)
    meta = extract_meta(soup)
    assert meta.og_title == "OG Title"


def test_h1_count():
    soup = _soup("<html><body><h1>First</h1><h1>Second</h1></body></html>")
    headings = extract_headings(soup)
    assert headings.h1_count == 2
    assert headings.h1_texts == ["First", "Second"]


def test_issues_for_missing_title():
    meta = MetaData(
        title=None, title_length=None, description="desc", description_length=4,
        canonical="/", robots_meta=None, og_title=None, og_description=None, og_image=None,
    )
    headings = HeadingStructure(h1_count=1, h2_count=0, h3_count=0, h1_texts=["Main"])
    issues = collect_issues(meta, headings)
    assert any(i.code == "MISSING_TITLE" for i in issues)


def test_issues_for_multiple_h1():
    meta = MetaData(
        title="A valid title here for SEO", title_length=26, description="x" * 130, description_length=130,
        canonical="/", robots_meta=None, og_title=None, og_description=None, og_image=None,
    )
    headings = HeadingStructure(h1_count=3, h2_count=0, h3_count=0, h1_texts=["a", "b", "c"])
    issues = collect_issues(meta, headings)
    assert any(i.code == "MULTIPLE_H1" for i in issues)


def test_parameterized_issue_exposes_structured_params():
    # The English message stays the deterministic source of truth; `params`
    # carries the same values structurally so clients can localize the template.
    meta = MetaData(
        title="short", title_length=5, description="x" * 130, description_length=130,
        canonical="/", robots_meta=None, og_title=None, og_description=None, og_image=None,
    )
    headings = HeadingStructure(h1_count=1, h2_count=0, h3_count=0, h1_texts=["Main"])
    issues = collect_issues(meta, headings)
    title_issue = next(i for i in issues if i.code == "TITLE_TOO_SHORT")
    assert title_issue.message == "Title too short (5 chars, min 30)"
    assert title_issue.params == {"length": 5, "min": 30}


def test_static_issue_has_empty_params():
    meta = MetaData(
        title=None, title_length=None, description="x" * 130, description_length=130,
        canonical="/", robots_meta=None, og_title=None, og_description=None, og_image=None,
    )
    headings = HeadingStructure(h1_count=1, h2_count=0, h3_count=0, h1_texts=["Main"])
    issues = collect_issues(meta, headings)
    title_issue = next(i for i in issues if i.code == "MISSING_TITLE")
    assert title_issue.params == {}


def test_score_deducted_by_severity():
    issues = [SeoIssue(code="X", severity="critical", message="x")]
    assert calculate_seo_score(issues) == 75


def test_score_floor_is_zero():
    issues = [SeoIssue(code=f"X{i}", severity="critical", message="x") for i in range(10)]
    assert calculate_seo_score(issues) == 0
