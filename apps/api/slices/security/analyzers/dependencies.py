from __future__ import annotations

import re

from slices.security.schemas import DependencyResult, SecurityFinding, Severity

# (library_name, filename_pattern)
JS_LIBRARY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("jQuery", re.compile(r"jquery[.\-](\d+\.\d+\.\d+)(?:\.min)?\.js", re.IGNORECASE)),
    ("Bootstrap", re.compile(r"bootstrap[.\-](\d+\.\d+\.\d+)(?:\.min)?\.(?:js|css)", re.IGNORECASE)),
    ("lodash", re.compile(r"lodash[.\-](\d+\.\d+\.\d+)(?:\.min)?\.js", re.IGNORECASE)),
    ("moment", re.compile(r"moment[.\-](\d+\.\d+\.\d+)(?:\.min)?\.js", re.IGNORECASE)),
    ("React", re.compile(r"react[.\-](\d+\.\d+\.\d+)(?:\.min)?\.js", re.IGNORECASE)),
    ("Vue", re.compile(r"vue[.\-](\d+\.\d+\.\d+)(?:\.min)?\.js", re.IGNORECASE)),
    ("Angular", re.compile(r"angular[.\-](\d+\.\d+\.\d+)(?:\.min)?\.js", re.IGNORECASE)),
]

# Minimum supported version per library; versions below are considered outdated
MINIMUM_VERSIONS: dict[str, tuple[int, ...]] = {
    "jQuery": (3, 0, 0),
    "Bootstrap": (5, 0, 0),
    "lodash": (4, 0, 0),
    "moment": (2, 29, 0),
}


def _parse_version(version_str: str) -> tuple[int, ...] | None:
    try:
        return tuple(int(x) for x in version_str.split("."))
    except (ValueError, AttributeError):
        return None


def analyze_dependencies(html: str) -> DependencyResult:
    detected_libraries: list[str] = []
    findings: list[SecurityFinding] = []

    for lib_name, pattern in JS_LIBRARY_PATTERNS:
        match = pattern.search(html)
        if not match:
            continue

        version_str = match.group(1)
        detected_libraries.append(f"{lib_name}@{version_str}")

        threshold = MINIMUM_VERSIONS.get(lib_name)
        parsed = _parse_version(version_str)

        if threshold and parsed and parsed < threshold:
            threshold_str = ".".join(str(x) for x in threshold)
            findings.append(
                SecurityFinding(
                    code="OUTDATED_JS_LIBRARY",
                    category="dependencies",
                    title=f"Outdated {lib_name} ({version_str})",
                    description=(
                        f"{lib_name} {version_str} is below the minimum recommended version "
                        f"{threshold_str} and may contain known vulnerabilities."
                    ),
                    severity=Severity.high,
                    params={"library": lib_name, "version": version_str, "minimum": threshold_str},
                    evidence=f"{lib_name}@{version_str}",
                    affected_resource=lib_name,
                    remediation=f"Upgrade {lib_name} to version {threshold_str} or later.",
                )
            )
        else:
            findings.append(
                SecurityFinding(
                    code="JS_LIBRARY_DETECTED",
                    category="dependencies",
                    title=f"JS library detected: {lib_name} {version_str}",
                    description=f"{lib_name} version {version_str} was detected in page assets.",
                    severity=Severity.informational,
                    params={"library": lib_name, "version": version_str},
                    evidence=f"{lib_name}@{version_str}",
                    affected_resource=lib_name,
                    remediation=None,
                )
            )

    score = 100
    for f in findings:
        if f.severity == Severity.high:
            score -= 25
    score = max(0, score)

    return DependencyResult(
        score=score,
        js_libraries=detected_libraries,
        findings=findings,
    )
