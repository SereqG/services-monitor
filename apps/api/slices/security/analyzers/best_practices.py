from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx

from slices.security.schemas import BestPracticesResult, SecurityFinding, Severity

_SECURITY_TXT_PATHS = ("/.well-known/security.txt", "/security.txt")

_EXPOSED_FILES: list[tuple[str, str, Severity]] = [
    ("/swagger.json", "Swagger API specification exposed publicly", Severity.medium),
    ("/openapi.json", "OpenAPI specification exposed publicly", Severity.medium),
    ("/api/swagger.json", "Swagger API specification exposed publicly", Severity.medium),
    ("/api/openapi.json", "OpenAPI specification exposed publicly", Severity.medium),
    ("/config.json", "Configuration file exposed publicly", Severity.high),
    ("/.env", "Environment file exposed publicly", Severity.critical),
    ("/phpinfo.php", "PHP info page exposed publicly", Severity.critical),
]

_SOURCEMAP_PATTERN = re.compile(r"sourceMappingURL=([^\s'\"]+\.map)", re.IGNORECASE)


async def _check_security_txt(client: httpx.AsyncClient, base_url: str) -> bool:
    for path in _SECURITY_TXT_PATHS:
        try:
            resp = await client.get(urljoin(base_url, path))
            if resp.status_code == 200 and "contact" in resp.text.lower():
                return True
        except httpx.HTTPError:
            pass
    return False


async def analyze_best_practices(
    client: httpx.AsyncClient,
    base_url: str,
    html: str,
    robots_txt_present: bool,
) -> BestPracticesResult:
    security_txt_present = await _check_security_txt(client, base_url)
    sourcemaps_found = _SOURCEMAP_PATTERN.findall(html)

    findings: list[SecurityFinding] = []

    if not security_txt_present:
        findings.append(
            SecurityFinding(
                category="best_practices",
                title="Missing security.txt",
                description="No security.txt found at /.well-known/security.txt or /security.txt.",
                severity=Severity.low,
                affected_resource=base_url,
                remediation="Create a security.txt file per RFC 9116 to define your vulnerability disclosure policy.",
            )
        )

    if sourcemaps_found:
        findings.append(
            SecurityFinding(
                category="best_practices",
                title="Source maps referenced in production assets",
                description=(
                    f"Found {len(sourcemaps_found)} sourceMappingURL reference(s) "
                    "that expose application source code."
                ),
                severity=Severity.medium,
                evidence="; ".join(sourcemaps_found[:3]),
                affected_resource=base_url,
                remediation="Disable source map generation or restrict access to .map files in production.",
            )
        )

    score = 100
    for f in findings:
        if f.severity == Severity.critical:
            score -= 40
        elif f.severity == Severity.high:
            score -= 25
        elif f.severity == Severity.medium:
            score -= 15
        elif f.severity == Severity.low:
            score -= 10
    score = max(0, score)

    return BestPracticesResult(
        score=score,
        security_txt_present=security_txt_present,
        robots_txt_present=robots_txt_present,
        sourcemaps_found=sourcemaps_found,
        findings=findings,
    )
