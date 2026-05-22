from __future__ import annotations

import re

import httpx

from slices.security.schemas import FrontendResult, SecurityFinding, Severity

# (name, source, pattern) — source is "html" or "header"
TECH_SIGNATURES: list[tuple[str, str, str]] = [
    ("WordPress", "html", r"wp-content"),
    ("Drupal", "html", r"Drupal\.settings|/sites/default/"),
    ("Next.js", "html", r"__NEXT_DATA__|/_next/"),
    ("React", "html", r"react\.production\.min\.js|__reactFiber"),
    ("Vue.js", "html", r"vue\.min\.js|__vue__"),
    ("Angular", "html", r'ng-version=|angular\.min\.js'),
    ("Bootstrap", "html", r"bootstrap\.min\.css|bootstrap\.bundle"),
    ("jQuery", "html", r"jquery[-.][\d.]+(?:\.min)?\.js"),
    ("Cloudflare", "header", r"cloudflare"),
    ("nginx", "header", r"nginx"),
    ("Apache", "header", r"apache"),
]


def _detect_technologies(html: str, response_headers: httpx.Headers) -> list[str]:
    detected: list[str] = []
    server_header = (
        response_headers.get("server", "")
        + " "
        + response_headers.get("x-powered-by", "")
    ).lower()

    for name, source, pattern in TECH_SIGNATURES:
        if source == "html":
            if re.search(pattern, html, re.IGNORECASE):
                detected.append(name)
        elif source == "header":
            if re.search(pattern, server_header, re.IGNORECASE):
                detected.append(name)

    return list(dict.fromkeys(detected))


def _check_mixed_content(html: str, page_url: str) -> list[SecurityFinding]:
    if not page_url.startswith("https://"):
        return []

    http_resources = re.findall(
        r'(?:src|href|action)=["\']http://[^"\']+["\']', html, re.IGNORECASE
    )
    if not http_resources:
        return []

    return [
        SecurityFinding(
            category="frontend",
            title="Mixed content detected",
            description=f"Found {len(http_resources)} HTTP resource(s) on an HTTPS page.",
            severity=Severity.medium,
            evidence="; ".join(http_resources[:3]),
            affected_resource=page_url,
            remediation="Serve all resources over HTTPS to prevent mixed content warnings.",
        )
    ]


def analyze_frontend(html: str, response_headers: httpx.Headers, page_url: str) -> FrontendResult:
    technologies = _detect_technologies(html, response_headers)
    findings: list[SecurityFinding] = []

    for tech in technologies:
        findings.append(
            SecurityFinding(
                category="frontend",
                title=f"Technology detected: {tech}",
                description=f"{tech} was identified on the page.",
                severity=Severity.informational,
                affected_resource=page_url,
                remediation=None,
            )
        )

    findings += _check_mixed_content(html, page_url)

    score = 100
    for f in findings:
        if f.severity == Severity.critical:
            score -= 40
        elif f.severity == Severity.high:
            score -= 25
        elif f.severity == Severity.medium:
            score -= 15
    score = max(0, score)

    return FrontendResult(
        score=score,
        technologies_detected=technologies,
        findings=findings,
    )
