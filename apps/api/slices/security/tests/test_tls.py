from __future__ import annotations

import asyncio
import datetime
import ssl
from unittest.mock import patch

from slices.security.analyzers.tls import analyze_tls
from slices.security.schemas import Severity


def _cert(days_from_now: int) -> dict:
    future = datetime.datetime.utcnow() + datetime.timedelta(days=days_from_now)
    return {"notAfter": future.strftime("%b %d %H:%M:%S %Y GMT")}


def test_http_url_gives_score_0_and_critical_finding():
    result = asyncio.run(analyze_tls("http://example.com"))
    assert result.score == 0
    assert len(result.findings) == 1
    assert result.findings[0].severity == Severity.critical
    assert result.tls_version is None


def test_valid_tls_1_3_cert_with_plenty_of_days_gives_score_100():
    with patch("slices.security.analyzers.tls._get_tls_info_blocking", return_value=("TLSv1.3", _cert(180))):
        result = asyncio.run(analyze_tls("https://example.com"))
    assert result.score == 100
    assert result.findings == []
    assert result.tls_version == "TLSv1.3"
    assert result.certificate_valid is True
    assert result.certificate_expiry_days is not None
    assert 178 <= result.certificate_expiry_days <= 180


def test_expired_cert_gives_critical_finding():
    with patch("slices.security.analyzers.tls._get_tls_info_blocking", return_value=("TLSv1.3", _cert(-1))):
        result = asyncio.run(analyze_tls("https://example.com"))
    assert result.certificate_valid is False
    critical = [f for f in result.findings if f.severity == Severity.critical]
    assert len(critical) == 1
    assert "expired" in critical[0].title.lower()
    assert result.score == 0


def test_cert_expiring_within_14_days_gives_high_finding():
    with patch("slices.security.analyzers.tls._get_tls_info_blocking", return_value=("TLSv1.3", _cert(7))):
        result = asyncio.run(analyze_tls("https://example.com"))
    high = [f for f in result.findings if f.severity == Severity.high]
    assert any("14 days" in f.title for f in high)


def test_cert_expiring_within_30_days_gives_medium_finding():
    with patch("slices.security.analyzers.tls._get_tls_info_blocking", return_value=("TLSv1.3", _cert(20))):
        result = asyncio.run(analyze_tls("https://example.com"))
    medium = [f for f in result.findings if f.severity == Severity.medium]
    assert any("30 days" in f.title for f in medium)


def test_weak_tls_version_gives_high_finding():
    for weak_version in ("TLSv1", "TLSv1.1"):
        with patch("slices.security.analyzers.tls._get_tls_info_blocking", return_value=(weak_version, _cert(180))):
            result = asyncio.run(analyze_tls("https://example.com"))
        high = [f for f in result.findings if f.severity == Severity.high]
        assert any(weak_version in f.title for f in high), f"Expected high finding for {weak_version}"


def test_ssl_cert_verification_error_gives_critical_finding():
    with patch(
        "slices.security.analyzers.tls._get_tls_info_blocking",
        side_effect=ssl.SSLCertVerificationError("cert verify failed"),
    ):
        result = asyncio.run(analyze_tls("https://example.com"))
    assert result.certificate_valid is False
    assert any(f.severity == Severity.critical for f in result.findings)


def test_ssl_error_gives_critical_finding():
    with patch(
        "slices.security.analyzers.tls._get_tls_info_blocking",
        side_effect=ssl.SSLError("handshake failed"),
    ):
        result = asyncio.run(analyze_tls("https://example.com"))
    assert any(f.severity == Severity.critical for f in result.findings)


def test_connection_refused_gives_informational_finding():
    with patch(
        "slices.security.analyzers.tls._get_tls_info_blocking",
        side_effect=ConnectionRefusedError("refused"),
    ):
        result = asyncio.run(analyze_tls("https://example.com"))
    assert any(f.severity == Severity.informational for f in result.findings)


def test_all_findings_have_category_tls():
    with patch("slices.security.analyzers.tls._get_tls_info_blocking", return_value=("TLSv1", _cert(-5))):
        result = asyncio.run(analyze_tls("https://example.com"))
    assert all(f.category == "tls" for f in result.findings)


def test_score_never_below_zero():
    with patch("slices.security.analyzers.tls._get_tls_info_blocking", return_value=("TLSv1", _cert(-1))):
        result = asyncio.run(analyze_tls("https://example.com"))
    assert result.score >= 0
