from __future__ import annotations

import httpx

from slices.security.schemas import CookieResult, SecurityFinding, Severity


def _parse_cookie_attributes(raw_cookie: str) -> dict[str, str | bool | None]:
    parts = [p.strip() for p in raw_cookie.split(";")]
    name = parts[0].split("=")[0].strip() if parts else ""
    secure = False
    httponly = False
    samesite: str | None = None

    for part in parts[1:]:
        lower = part.lower().strip()
        if lower == "secure":
            secure = True
        elif lower == "httponly":
            httponly = True
        elif lower.startswith("samesite="):
            samesite = part.split("=", 1)[1].strip().lower()

    return {"name": name, "secure": secure, "httponly": httponly, "samesite": samesite}


def analyze_cookies(response_headers: httpx.Headers) -> CookieResult:
    cookie_headers = response_headers.get_list("set-cookie")

    if not cookie_headers:
        return CookieResult(score=100, total_cookies=0, findings=[])

    findings: list[SecurityFinding] = []

    for raw_cookie in cookie_headers:
        attrs = _parse_cookie_attributes(raw_cookie)
        name = str(attrs["name"])

        if not attrs["secure"]:
            findings.append(
                SecurityFinding(
                    code="COOKIE_MISSING_SECURE",
                    category="cookies",
                    title=f"Missing Secure flag on cookie '{name}'",
                    description="Cookie can be transmitted over unencrypted HTTP connections.",
                    severity=Severity.medium,
                    params={"cookie": name},
                    evidence=raw_cookie,
                    affected_resource=name,
                    remediation="Add the Secure flag to cookies that should only be sent over HTTPS.",
                )
            )

        if not attrs["httponly"]:
            findings.append(
                SecurityFinding(
                    code="COOKIE_MISSING_HTTPONLY",
                    category="cookies",
                    title=f"Missing HttpOnly flag on cookie '{name}'",
                    description="Cookie is accessible via JavaScript, increasing XSS risk.",
                    severity=Severity.medium,
                    params={"cookie": name},
                    evidence=raw_cookie,
                    affected_resource=name,
                    remediation="Add the HttpOnly flag to cookies that do not require JavaScript access.",
                )
            )

        samesite = attrs["samesite"]
        if samesite is None:
            findings.append(
                SecurityFinding(
                    code="COOKIE_MISSING_SAMESITE",
                    category="cookies",
                    title=f"Missing SameSite attribute on cookie '{name}'",
                    description="Cookie is sent on all cross-origin requests, increasing CSRF risk.",
                    severity=Severity.medium,
                    params={"cookie": name},
                    evidence=raw_cookie,
                    affected_resource=name,
                    remediation="Set SameSite=Strict or SameSite=Lax on session cookies.",
                )
            )
        elif samesite == "none" and not attrs["secure"]:
            findings.append(
                SecurityFinding(
                    code="COOKIE_SAMESITE_NONE_INSECURE",
                    category="cookies",
                    title=f"SameSite=None without Secure on cookie '{name}'",
                    description="SameSite=None is invalid without the Secure flag.",
                    severity=Severity.high,
                    params={"cookie": name},
                    evidence=raw_cookie,
                    affected_resource=name,
                    remediation="Add the Secure flag when using SameSite=None.",
                )
            )

    score = 100
    for f in findings:
        if f.severity == Severity.high:
            score -= 20
        elif f.severity == Severity.medium:
            score -= 10
    score = max(0, score)

    return CookieResult(score=score, total_cookies=len(cookie_headers), findings=findings)
