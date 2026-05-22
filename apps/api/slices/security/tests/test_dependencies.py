from __future__ import annotations

from slices.security.analyzers.dependencies import (
    MINIMUM_VERSIONS,
    analyze_dependencies,
    _parse_version,
)
from slices.security.schemas import Severity


def test_no_libraries_detected_gives_score_100():
    result = analyze_dependencies("<html><body>hello</body></html>")
    assert result.score == 100
    assert result.js_libraries == []
    assert result.findings == []


def test_detects_jquery_version_in_script_src():
    html = '<html><head><script src="/js/jquery-3.6.0.min.js"></script></head></html>'
    result = analyze_dependencies(html)
    assert "jQuery@3.6.0" in result.js_libraries


def test_outdated_jquery_gives_high_finding():
    html = '<html><head><script src="/js/jquery-1.12.4.min.js"></script></head></html>'
    result = analyze_dependencies(html)
    high = [f for f in result.findings if f.severity == Severity.high]
    assert len(high) == 1
    assert "jQuery" in high[0].title
    assert "1.12.4" in high[0].title


def test_current_jquery_gives_informational_finding():
    html = '<html><head><script src="/js/jquery-3.7.0.min.js"></script></head></html>'
    result = analyze_dependencies(html)
    info = [f for f in result.findings if f.severity == Severity.informational]
    assert any("jQuery" in f.title for f in info)
    high = [f for f in result.findings if f.severity == Severity.high]
    assert high == []


def test_outdated_bootstrap_gives_high_finding():
    html = '<html><head><link href="/css/bootstrap-4.6.0.min.css"/></head></html>'
    result = analyze_dependencies(html)
    high = [f for f in result.findings if f.severity == Severity.high]
    assert any("Bootstrap" in f.title for f in high)


def test_score_reduced_per_outdated_library():
    html = '<html><head><script src="/jquery-1.0.0.min.js"></script></head></html>'
    result = analyze_dependencies(html)
    assert result.score < 100


def test_score_floor_is_zero():
    libs = " ".join(
        f'<script src="/jquery-1.0.{i}.min.js"></script>'
        for i in range(10)
    )
    html = f"<html><head>{libs}</head></html>"
    result = analyze_dependencies(html)
    assert result.score >= 0


def test_findings_category_is_dependencies():
    html = '<html><head><script src="/jquery-1.0.0.min.js"></script></head></html>'
    result = analyze_dependencies(html)
    assert all(f.category == "dependencies" for f in result.findings)


def test_parse_version_returns_tuple():
    assert _parse_version("3.6.0") == (3, 6, 0)


def test_parse_version_returns_none_for_invalid():
    assert _parse_version("not-a-version") is None


def test_minimum_versions_defined_for_major_libs():
    assert "jQuery" in MINIMUM_VERSIONS
    assert "Bootstrap" in MINIMUM_VERSIONS
