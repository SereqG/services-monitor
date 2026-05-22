from __future__ import annotations

import httpx

from slices.security.schemas import HeadersResult, SecurityFinding, Severity

# (header_name, missing_severity, description, remediation)
SECURITY_HEADERS: list[tuple[str, Severity, str, str]] = [
    (
        "Content-Security-Policy",
        Severity.high,
        "Restricts content sources to prevent XSS and data injection attacks.",
        "Define a strict Content-Security-Policy header; avoid unsafe-inline and wildcards.",
    ),
    (
        "Strict-Transport-Security",
        Severity.high,
        "Enforces HTTPS and protects against protocol downgrade attacks.",
        "Add Strict-Transport-Security with max-age of at least 31536000.",
    ),
    (
        "X-Frame-Options",
        Severity.medium,
        "Prevents clickjacking by controlling page embedding in frames.",
        "Set X-Frame-Options to DENY or SAMEORIGIN.",
    ),
    (
        "X-Content-Type-Options",
        Severity.medium,
        "Prevents MIME-sniffing away from the declared content type.",
        "Set X-Content-Type-Options: nosniff.",
    ),
    (
        "Referrer-Policy",
        Severity.medium,
        "Controls how much referrer information is included with requests.",
        "Set Referrer-Policy to strict-origin-when-cross-origin or stricter.",
    ),
    (
        "Permissions-Policy",
        Severity.low,
        "Restricts browser API access such as camera and geolocation.",
        "Add a Permissions-Policy header to disable features not used by the application.",
    ),
    (
        "Cross-Origin-Opener-Policy",
        Severity.low,
        "Isolates the browsing context to prevent cross-origin attacks.",
        "Set Cross-Origin-Opener-Policy: same-origin.",
    ),
    (
        "Cross-Origin-Embedder-Policy",
        Severity.low,
        "Prevents loading cross-origin resources without explicit permission.",
        "Set Cross-Origin-Embedder-Policy: require-corp.",
    ),
    (
        "Cross-Origin-Resource-Policy",
        Severity.low,
        "Controls which origins can load this resource.",
        "Set Cross-Origin-Resource-Policy: same-origin or same-site.",
    ),
]


def analyze_headers(response_headers: httpx.Headers) -> HeadersResult:
    headers_present: list[str] = []
    headers_missing: list[str] = []
    findings: list[SecurityFinding] = []

    for header_name, severity, description, remediation in SECURITY_HEADERS:
        if header_name.lower() in response_headers:
            headers_present.append(header_name)
        else:
            headers_missing.append(header_name)
            findings.append(
                SecurityFinding(
                    category="headers",
                    title=f"Missing {header_name}",
                    description=description,
                    severity=severity,
                    affected_resource=header_name,
                    remediation=remediation,
                )
            )

    score = round(len(headers_present) / len(SECURITY_HEADERS) * 100)
    return HeadersResult(
        score=score,
        headers_present=headers_present,
        headers_missing=headers_missing,
        findings=findings,
    )
