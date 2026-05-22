from __future__ import annotations

import httpx

from slices.security.analyzers.cookies import analyze_cookies, _parse_cookie_attributes
from slices.security.schemas import Severity


def _headers(cookies: list[str]) -> httpx.Headers:
    raw = [(b"set-cookie", c.encode()) for c in cookies]
    return httpx.Headers(raw)


def test_no_cookies_gives_score_100():
    result = analyze_cookies(httpx.Headers({}))
    assert result.score == 100
    assert result.total_cookies == 0
    assert result.findings == []


def test_cookie_with_all_flags_produces_no_findings():
    result = analyze_cookies(_headers(["session=abc; Secure; HttpOnly; SameSite=Strict"]))
    assert result.findings == []
    assert result.score == 100
    assert result.total_cookies == 1


def test_missing_secure_flag_gives_medium_finding():
    result = analyze_cookies(_headers(["session=abc; HttpOnly; SameSite=Strict"]))
    secure_findings = [f for f in result.findings if "Secure" in f.title]
    assert len(secure_findings) == 1
    assert secure_findings[0].severity == Severity.medium


def test_missing_httponly_flag_gives_medium_finding():
    result = analyze_cookies(_headers(["session=abc; Secure; SameSite=Strict"]))
    httponly_findings = [f for f in result.findings if "HttpOnly" in f.title]
    assert len(httponly_findings) == 1
    assert httponly_findings[0].severity == Severity.medium


def test_missing_samesite_gives_medium_finding():
    result = analyze_cookies(_headers(["session=abc; Secure; HttpOnly"]))
    samesite_findings = [f for f in result.findings if "SameSite" in f.title]
    assert len(samesite_findings) == 1
    assert samesite_findings[0].severity == Severity.medium


def test_samesite_none_without_secure_gives_high_finding():
    result = analyze_cookies(_headers(["session=abc; HttpOnly; SameSite=None"]))
    high_findings = [f for f in result.findings if f.severity == Severity.high]
    assert len(high_findings) == 1
    assert "SameSite=None" in high_findings[0].title


def test_samesite_none_with_secure_is_valid():
    result = analyze_cookies(_headers(["session=abc; Secure; HttpOnly; SameSite=None"]))
    samesite_none_high = [f for f in result.findings if f.severity == Severity.high]
    assert samesite_none_high == []


def test_multiple_cookies_each_produce_findings():
    result = analyze_cookies(_headers([
        "a=1; Secure; HttpOnly; SameSite=Strict",
        "b=2",
    ]))
    assert result.total_cookies == 2
    assert len([f for f in result.findings if "Secure" in f.title]) == 1
    assert len([f for f in result.findings if "HttpOnly" in f.title]) == 1


def test_score_decreases_per_finding():
    result = analyze_cookies(_headers(["session=abc"]))
    assert result.score < 100


def test_score_floor_is_zero():
    many_bad = ["bad%d=x" % i for i in range(20)]
    result = analyze_cookies(_headers(many_bad))
    assert result.score >= 0


def test_findings_category_is_cookies():
    result = analyze_cookies(_headers(["session=abc"]))
    assert all(f.category == "cookies" for f in result.findings)


def test_parse_cookie_attributes_extracts_name():
    attrs = _parse_cookie_attributes("session=abc123; Secure; HttpOnly")
    assert attrs["name"] == "session"


def test_parse_cookie_attributes_detects_flags():
    attrs = _parse_cookie_attributes("x=y; Secure; HttpOnly; SameSite=Lax")
    assert attrs["secure"] is True
    assert attrs["httponly"] is True
    assert attrs["samesite"] == "lax"


def test_parse_cookie_attributes_handles_missing_flags():
    attrs = _parse_cookie_attributes("x=y")
    assert attrs["secure"] is False
    assert attrs["httponly"] is False
    assert attrs["samesite"] is None
