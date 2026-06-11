from __future__ import annotations

import httpx

from slices.security.analyzers.headers import SECURITY_HEADERS, analyze_headers
from slices.security.schemas import Severity

ALL_HEADER_NAMES = {name for name, _, _, _ in SECURITY_HEADERS}
_ALL_PRESENT = httpx.Headers({name: "present" for name, _, _, _ in SECURITY_HEADERS})
_NONE_PRESENT = httpx.Headers({})


def test_all_headers_present_gives_score_100():
    result = analyze_headers(_ALL_PRESENT)
    assert result.score == 100
    assert set(result.headers_present) == ALL_HEADER_NAMES
    assert result.headers_missing == []
    assert result.findings == []


def test_no_headers_gives_score_0():
    result = analyze_headers(_NONE_PRESENT)
    assert result.score == 0
    assert result.headers_present == []
    assert set(result.headers_missing) == ALL_HEADER_NAMES
    assert len(result.findings) == len(SECURITY_HEADERS)


def test_partial_headers_give_proportional_score():
    present_count = 3
    partial = httpx.Headers({name: "x" for name, _, _, _ in SECURITY_HEADERS[:present_count]})
    result = analyze_headers(partial)
    expected = round(present_count / len(SECURITY_HEADERS) * 100)
    assert result.score == expected


def test_missing_csp_produces_high_severity_finding():
    headers_without_csp = httpx.Headers(
        {name: "x" for name, _, _, _ in SECURITY_HEADERS if name != "Content-Security-Policy"}
    )
    result = analyze_headers(headers_without_csp)
    csp_finding = next(f for f in result.findings if "Content-Security-Policy" in f.title)
    assert csp_finding.severity == Severity.high


def test_missing_hsts_produces_high_severity_finding():
    headers_without_hsts = httpx.Headers(
        {name: "x" for name, _, _, _ in SECURITY_HEADERS if name != "Strict-Transport-Security"}
    )
    result = analyze_headers(headers_without_hsts)
    hsts_finding = next(f for f in result.findings if "Strict-Transport-Security" in f.title)
    assert hsts_finding.severity == Severity.high


def test_missing_x_frame_options_produces_medium_severity():
    headers = httpx.Headers(
        {name: "x" for name, _, _, _ in SECURITY_HEADERS if name != "X-Frame-Options"}
    )
    result = analyze_headers(headers)
    finding = next(f for f in result.findings if "X-Frame-Options" in f.title)
    assert finding.severity == Severity.medium


def test_missing_coop_produces_low_severity():
    headers = httpx.Headers(
        {name: "x" for name, _, _, _ in SECURITY_HEADERS if name != "Cross-Origin-Opener-Policy"}
    )
    result = analyze_headers(headers)
    finding = next(f for f in result.findings if "Cross-Origin-Opener-Policy" in f.title)
    assert finding.severity == Severity.low


def test_finding_category_is_headers():
    result = analyze_headers(_NONE_PRESENT)
    assert all(f.category == "headers" for f in result.findings)


def test_finding_includes_remediation():
    result = analyze_headers(_NONE_PRESENT)
    assert all(f.remediation is not None for f in result.findings)


def test_finding_carries_stable_code_and_params():
    # Code + params are the localization contract; the English title is unchanged.
    result = analyze_headers(_NONE_PRESENT)
    csp = next(f for f in result.findings if f.params.get("header") == "Content-Security-Policy")
    assert csp.code == "MISSING_SECURITY_HEADER"
    assert csp.title == "Missing Content-Security-Policy"
    assert all(f.code == "MISSING_SECURITY_HEADER" for f in result.findings)


def test_nine_headers_checked():
    assert len(SECURITY_HEADERS) == 9


def test_header_check_is_case_insensitive():
    lower_headers = httpx.Headers(
        {name.lower(): "x" for name, _, _, _ in SECURITY_HEADERS}
    )
    result = analyze_headers(lower_headers)
    assert result.score == 100
