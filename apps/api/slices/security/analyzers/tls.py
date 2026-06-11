from __future__ import annotations

import asyncio
import datetime
import socket
import ssl
from urllib.parse import urlparse

from slices.security.schemas import SecurityFinding, Severity, TlsResult

WEAK_TLS_VERSIONS = {"SSLv2", "SSLv3", "TLSv1", "TLSv1.1"}


def _get_tls_info_blocking(hostname: str, port: int) -> tuple[str | None, dict | None]:
    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.create_connection((hostname, port), timeout=10),
        server_hostname=hostname,
    )
    try:
        return conn.version(), conn.getpeercert()
    finally:
        conn.close()


def _score_from_findings(findings: list[SecurityFinding]) -> int:
    if any(f.severity == Severity.critical for f in findings):
        return 0
    score = 100
    for f in findings:
        if f.severity == Severity.high:
            score -= 30
        elif f.severity == Severity.medium:
            score -= 15
    return max(0, score)


async def analyze_tls(url: str) -> TlsResult:
    parsed = urlparse(url)

    if parsed.scheme != "https":
        return TlsResult(
            score=0,
            tls_version=None,
            certificate_valid=None,
            certificate_expiry_days=None,
            findings=[
                SecurityFinding(
                    code="HTTPS_NOT_USED",
                    category="tls",
                    title="HTTPS not used",
                    description="The target URL does not use HTTPS, exposing traffic to interception.",
                    severity=Severity.critical,
                    affected_resource=url,
                    remediation="Redirect all HTTP traffic to HTTPS and configure a valid TLS certificate.",
                )
            ],
        )

    hostname = parsed.hostname or ""
    port = parsed.port or 443
    findings: list[SecurityFinding] = []
    tls_version: str | None = None
    certificate_valid: bool | None = None
    certificate_expiry_days: int | None = None

    try:
        loop = asyncio.get_event_loop()
        tls_version, cert = await loop.run_in_executor(None, _get_tls_info_blocking, hostname, port)

        if tls_version in WEAK_TLS_VERSIONS:
            findings.append(
                SecurityFinding(
                    code="WEAK_TLS_VERSION",
                    category="tls",
                    title=f"Weak TLS version: {tls_version}",
                    description=f"{tls_version} is deprecated and cryptographically weak.",
                    severity=Severity.high,
                    params={"version": tls_version or ""},
                    evidence=tls_version,
                    affected_resource=url,
                    remediation="Disable TLS 1.0 and TLS 1.1. Require TLS 1.2 or TLS 1.3.",
                )
            )

        certificate_valid = True
        if cert and "notAfter" in cert:
            expiry = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            now = datetime.datetime.utcnow()
            days_left = (expiry - now).days
            certificate_expiry_days = days_left

            if days_left < 0:
                certificate_valid = False
                findings.append(
                    SecurityFinding(
                        code="TLS_CERT_EXPIRED",
                        category="tls",
                        title="Expired TLS certificate",
                        description="The TLS certificate has expired and will cause browser errors.",
                        severity=Severity.critical,
                        params={"days": abs(days_left)},
                        evidence=f"Expired {abs(days_left)} day(s) ago",
                        affected_resource=hostname,
                        remediation="Renew the TLS certificate immediately.",
                    )
                )
            elif days_left < 14:
                findings.append(
                    SecurityFinding(
                        code="TLS_CERT_EXPIRING_SOON",
                        category="tls",
                        title="TLS certificate expiring within 14 days",
                        description=f"Certificate expires in {days_left} day(s).",
                        severity=Severity.high,
                        params={"days": days_left},
                        evidence=f"{days_left} day(s) remaining",
                        affected_resource=hostname,
                        remediation="Renew the TLS certificate before expiry.",
                    )
                )
            elif days_left < 30:
                findings.append(
                    SecurityFinding(
                        code="TLS_CERT_EXPIRING",
                        category="tls",
                        title="TLS certificate expiring within 30 days",
                        description=f"Certificate expires in {days_left} day(s).",
                        severity=Severity.medium,
                        params={"days": days_left},
                        evidence=f"{days_left} day(s) remaining",
                        affected_resource=hostname,
                        remediation="Plan to renew the TLS certificate.",
                    )
                )

    except ssl.SSLCertVerificationError as exc:
        certificate_valid = False
        findings.append(
            SecurityFinding(
                code="TLS_CERT_VERIFICATION_FAILED",
                category="tls",
                title="TLS certificate verification failed",
                description=f"SSL verification error: {exc}",
                severity=Severity.critical,
                params={"error": str(exc)},
                evidence=str(exc),
                affected_resource=url,
                remediation="Fix the TLS certificate (check chain, hostname, expiry).",
            )
        )
    except ssl.SSLError as exc:
        findings.append(
            SecurityFinding(
                code="TLS_HANDSHAKE_FAILED",
                category="tls",
                title="TLS handshake failed",
                description=f"SSL error during connection: {exc}",
                severity=Severity.critical,
                params={"error": str(exc)},
                evidence=str(exc),
                affected_resource=url,
                remediation="Investigate and fix the TLS configuration.",
            )
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        findings.append(
            SecurityFinding(
                code="TLS_UNREACHABLE",
                category="tls",
                title="TLS connection unreachable",
                description=f"Could not connect to check TLS: {exc}",
                severity=Severity.informational,
                params={"error": str(exc)},
                evidence=str(exc),
                affected_resource=url,
                remediation="Verify the host is accessible and TLS is configured.",
            )
        )

    return TlsResult(
        score=_score_from_findings(findings),
        tls_version=tls_version,
        certificate_valid=certificate_valid,
        certificate_expiry_days=certificate_expiry_days,
        findings=findings,
    )
