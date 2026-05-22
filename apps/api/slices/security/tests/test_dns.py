from __future__ import annotations

import asyncio
from unittest.mock import patch

import dns.exception

from slices.security.analyzers.dns import (
    _has_caa,
    _has_dmarc,
    _has_dnssec,
    _has_spf,
    analyze_dns,
)
from slices.security.schemas import Severity


class _FakeTxtRecord:
    def __init__(self, value: str):
        self.strings = [value.encode()]


class _FakeAnswer:
    def __init__(self, records: list[_FakeTxtRecord]):
        self._records = records

    def __iter__(self):
        return iter(self._records)


def test_all_dns_records_present_gives_score_100():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=True),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=True),
        patch("slices.security.analyzers.dns._has_caa", return_value=True),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=True),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    assert result.score == 100
    assert result.findings == []
    assert result.spf_present is True
    assert result.dmarc_present is True
    assert result.caa_present is True
    assert result.dnssec_enabled is True


def test_no_dns_records_gives_score_0_and_four_findings():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=False),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=False),
        patch("slices.security.analyzers.dns._has_caa", return_value=False),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=False),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    assert result.score == 0
    assert len(result.findings) == 4


def test_missing_spf_gives_medium_finding():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=False),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=True),
        patch("slices.security.analyzers.dns._has_caa", return_value=True),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=True),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    spf_finding = next(f for f in result.findings if "SPF" in f.title)
    assert spf_finding.severity == Severity.medium


def test_missing_dmarc_gives_medium_finding():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=True),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=False),
        patch("slices.security.analyzers.dns._has_caa", return_value=True),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=True),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    dmarc_finding = next(f for f in result.findings if "DMARC" in f.title)
    assert dmarc_finding.severity == Severity.medium


def test_missing_caa_gives_low_finding():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=True),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=True),
        patch("slices.security.analyzers.dns._has_caa", return_value=False),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=True),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    caa_finding = next(f for f in result.findings if "CAA" in f.title)
    assert caa_finding.severity == Severity.low


def test_missing_dnssec_gives_low_finding():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=True),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=True),
        patch("slices.security.analyzers.dns._has_caa", return_value=True),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=False),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    dnssec_finding = next(f for f in result.findings if "DNSSEC" in f.title)
    assert dnssec_finding.severity == Severity.low


def test_score_is_proportional_to_checks_passed():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=True),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=True),
        patch("slices.security.analyzers.dns._has_caa", return_value=False),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=False),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    assert result.score == 50


def test_has_spf_detects_spf_record():
    with patch("dns.resolver.resolve", return_value=_FakeAnswer([_FakeTxtRecord("v=spf1 include:example.com -all")])):
        assert _has_spf("example.com") is True


def test_has_spf_returns_false_when_no_spf():
    with patch("dns.resolver.resolve", return_value=_FakeAnswer([_FakeTxtRecord("not-spf")])):
        assert _has_spf("example.com") is False


def test_has_dmarc_detects_dmarc_record():
    with patch("dns.resolver.resolve", return_value=_FakeAnswer([_FakeTxtRecord("v=DMARC1; p=quarantine")])):
        assert _has_dmarc("example.com") is True


def test_has_spf_returns_false_on_dns_exception():
    with patch("dns.resolver.resolve", side_effect=dns.exception.DNSException()):
        assert _has_spf("example.com") is False


def test_findings_category_is_dns():
    with (
        patch("slices.security.analyzers.dns._has_spf", return_value=False),
        patch("slices.security.analyzers.dns._has_dmarc", return_value=False),
        patch("slices.security.analyzers.dns._has_caa", return_value=False),
        patch("slices.security.analyzers.dns._has_dnssec", return_value=False),
    ):
        result = asyncio.run(analyze_dns("example.com"))
    assert all(f.category == "dns" for f in result.findings)
