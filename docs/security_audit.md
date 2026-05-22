# Security Audit Service — Technical Reference for Claude Code

## Purpose

This document defines:

* architecture assumptions,
* implementation boundaries,
* legal and safety constraints,
* passive security audit workflow,
* metrics and scoring system,
* crawler behavior,
* analysis pipeline,
* reporting standards,
* implementation guidelines.

This document is intended to serve as a long-term implementation reference for Claude Code.

---

# 1. Project Goals

The system is designed as:

* passive security auditor,
* compliance-first crawler,
* non-invasive website analysis platform,
* automated web security assessment service.

The system MUST:

* remain fully legal,
* avoid offensive security behavior,
* avoid disruption of target infrastructure,
* avoid exploit execution,
* respect robots.txt,
* operate with strict rate limiting,
* provide deterministic findings whenever possible.

The project focuses on:

* security hygiene,
* configuration analysis,
* exposure detection,
* dependency risk analysis,
* infrastructure hardening validation,
* frontend exposure discovery.

---

# 2. High-Level Architecture

## Backend

Preferred stack:

* Python
* FastAPI
* asyncio
* httpx
* Playwright
* selectolax or lxml

## Frontend

Preferred stack:

* Next.js
* React
* TypeScript

## System Characteristics

The system should:

* support async execution,
* support distributed workers in future,
* support scheduled audits,
* support historical comparison,
* support incremental rescans,
* expose REST API,
* produce deterministic reports.

---

# 3. Legal and Ethical Constraints

The crawler MUST:

* respect robots.txt,
* identify itself via User-Agent,
* implement request throttling,
* implement retry policies,
* implement crawl depth limits,
* implement request budgets,
* avoid authentication bypass attempts,
* avoid brute force,
* avoid fuzzing,
* avoid exploit execution,
* avoid active port scanning,
* avoid payload injection,
* avoid vulnerability exploitation.

The platform is designed for:

* passive analysis only,
* publicly accessible resources only,
* deterministic non-invasive assessment.

---

# 4. Audit Workflow

## Phase 1 — Target Initialization

Input:

* URL
* domain
* optional configuration

Validation:

* normalize URL,
* validate scheme,
* reject invalid hosts,
* enforce HTTPS where possible.

---

## Phase 2 — robots.txt Processing

The crawler MUST:

* fetch robots.txt,
* parse robots rules,
* respect disallowed paths,
* apply crawl restrictions.

Additional parsing:

* sitemap locations,
* crawl-delay,
* discovered endpoints.

---

## Phase 3 — Passive Discovery

Safe discovery only.

Discovery includes:

* homepage fetch,
* limited internal crawling,
* sitemap parsing,
* asset enumeration,
* script extraction,
* stylesheet extraction,
* metadata extraction.

The crawler MUST:

* limit recursion depth,
* avoid infinite loops,
* avoid aggressive crawling,
* respect request budgets.

---

## Phase 4 — Infrastructure Analysis

Infrastructure analysis includes:

* TLS analysis,
* DNS analysis,
* CDN detection,
* WAF detection,
* HTTP server fingerprinting.

---

## Phase 5 — Frontend Analysis

Frontend analysis includes:

* JavaScript library detection,
* framework detection,
* sourcemap detection,
* exposed configuration discovery,
* endpoint extraction,
* secret pattern detection,
* mixed content analysis.

---

## Phase 6 — Security Header Analysis

Headers are collected and validated.

Analysis includes:

* presence,
* correctness,
* strictness,
* security impact.

---

## Phase 7 — Scoring and Severity Calculation

Findings are normalized into:

* informational,
* low,
* medium,
* high,
* critical.

A global security score is calculated.

---

## Phase 8 — Report Generation

Reports should support:

* JSON,
* Markdown,
* PDF,
* CSV exports.

Reports should contain:

* findings,
* severity,
* evidence,
* affected resources,
* remediation guidance,
* historical comparison.

---

# 5. Core Security Metrics

Most metrics should be implemented deterministically without AI.

---

# 6. TLS / HTTPS Metrics

## Objective

Validate transport security configuration.

## Implementation

Use:

* ssl module,
* OpenSSL,
* sslyze.

## Metrics

| Metric                 | Description              |
| ---------------------- | ------------------------ |
| TLS version            | Supported TLS versions   |
| Weak ciphers           | Deprecated cipher suites |
| Certificate validity   | X509 validity            |
| Certificate expiration | Remaining validity days  |
| HSTS enabled           | Presence of HSTS         |
| Forward secrecy        | Modern cipher support    |
| OCSP stapling          | OCSP support             |
| Key length             | RSA/ECDSA key strength   |

## Findings

Examples:

* TLS 1.0 enabled,
* expired certificate,
* weak cipher support,
* missing HSTS.

---

# 7. Security Headers

## Objective

Validate browser security hardening.

## Headers

| Header                       | Purpose                  |
| ---------------------------- | ------------------------ |
| Content-Security-Policy      | XSS mitigation           |
| Strict-Transport-Security    | HTTPS enforcement        |
| X-Frame-Options              | Clickjacking protection  |
| X-Content-Type-Options       | MIME sniffing prevention |
| Referrer-Policy              | Referrer protection      |
| Permissions-Policy           | Browser API restrictions |
| Cross-Origin-Opener-Policy   | Cross-origin isolation   |
| Cross-Origin-Embedder-Policy | Resource isolation       |
| Cross-Origin-Resource-Policy | Resource sharing control |

## Implementation

Headers should be:

* parsed,
* normalized,
* validated,
* scored.

## Scoring Considerations

Examples:

* missing CSP,
* unsafe-inline usage,
* wildcard policies,
* weak HSTS max-age.

---

# 8. Cookie Security

## Objective

Validate session and cookie hardening.

## Metrics

| Metric          | Description          |
| --------------- | -------------------- |
| Secure flag     | HTTPS-only cookies   |
| HttpOnly flag   | JS access prevention |
| SameSite policy | CSRF mitigation      |
| Expiration time | Session lifetime     |
| Domain scope    | Cookie exposure      |
| Path scope      | Cookie accessibility |

## Findings

Examples:

* missing Secure flag,
* missing HttpOnly,
* SameSite=None without Secure,
* excessive expiration duration.

---

# 9. DNS Security Metrics

## Objective

Validate DNS and email security posture.

## Metrics

| Metric       | Description              |
| ------------ | ------------------------ |
| SPF          | Sender validation        |
| DKIM         | Email signing            |
| DMARC        | Anti-spoofing policy     |
| DNSSEC       | DNS integrity            |
| CAA          | Certificate restrictions |
| MX records   | Mail configuration       |
| IPv6 support | Network support          |

## Implementation

Use:

* dnspython,
* async DNS resolvers.

---

# 10. Technology Fingerprinting

## Objective

Identify application stack.

## Detection Sources

* headers,
* HTML patterns,
* JS globals,
* script names,
* meta tags,
* asset naming.

## Technologies

Examples:

* WordPress,
* Next.js,
* React,
* Vue,
* FastAPI,
* nginx,
* Cloudflare.

## Implementation

Rule-based fingerprinting only.

No AI required.

---

# 11. Dependency and Library Analysis

## Objective

Detect outdated or vulnerable frontend dependencies.

## Sources

* script filenames,
* package metadata,
* sourcemaps,
* inline version references.

## Metrics

| Metric             | Description               |
| ------------------ | ------------------------- |
| Outdated libraries | Unsupported versions      |
| Known CVEs         | Public vulnerabilities    |
| Severity count     | Number of vulnerable libs |
| Dependency age     | Maintenance status        |

## CVE Sources

Possible integrations:

* NVD,
* OSV,
* GitHub advisories.

---

# 12. Public Exposure Detection

## Objective

Detect unintentionally exposed public resources.

## Targets

| Resource     | Risk                   |
| ------------ | ---------------------- |
| .map files   | Source disclosure      |
| config.json  | Internal configuration |
| swagger.json | API exposure           |
| openapi.json | API exposure           |
| security.txt | Disclosure policy      |
| robots.txt   | Endpoint exposure      |
| sitemap.xml  | Surface discovery      |

## Important

The system MUST:

* only verify public accessibility,
* avoid exploitation,
* avoid authentication bypass attempts.

---

# 13. Frontend Security Analysis

## Objective

Analyze frontend exposure and unsafe patterns.

## Metrics

| Metric               | Description                |
| -------------------- | -------------------------- |
| Mixed content        | HTTP assets on HTTPS pages |
| Inline scripts       | CSP weakening              |
| External domains     | Third-party exposure       |
| Public endpoints     | API exposure               |
| Third-party trackers | Privacy impact             |
| Debug artifacts      | Development leftovers      |

## Secret Detection

Use:

* regex,
* entropy heuristics,
* pattern matching.

Examples:

* AWS keys,
* JWT tokens,
* API tokens.

---

# 14. WAF and CDN Detection

## Objective

Identify infrastructure protection layers.

## Detection Sources

* headers,
* response signatures,
* DNS,
* CDN domains.

## Possible Findings

| Finding             | Meaning                |
| ------------------- | ---------------------- |
| Cloudflare detected | CDN/WAF present        |
| No WAF detected     | Reduced protection     |
| CDN absent          | Direct origin exposure |

---

# 15. Crawl Safety Requirements

## Mandatory Limits

| Limit              | Purpose                 |
| ------------------ | ----------------------- |
| Max crawl depth    | Prevent recursion       |
| Request budget     | Prevent overload        |
| Rate limiting      | Prevent abuse           |
| Concurrency limits | Infrastructure safety   |
| Retry caps         | Avoid excessive traffic |

## Recommended Defaults

| Setting        | Value        |
| -------------- | ------------ |
| Max depth      | 2-3          |
| Concurrency    | 2-5          |
| Delay          | 500ms-2000ms |
| Total requests | 50-200       |

---

# 16. Scoring System

## Example Global Security Score

Range:

* 0-100

## Suggested Weighting

| Category          | Weight |
| ----------------- | ------ |
| TLS               | 20     |
| Security headers  | 20     |
| Cookie security   | 10     |
| DNS security      | 10     |
| Frontend exposure | 15     |
| Dependency risk   | 15     |
| Best practices    | 10     |

---

# 17. Severity Classification

## Critical

Examples:

* exposed secrets,
* expired certificate,
* public admin credentials.

## High

Examples:

* vulnerable JS libraries,
* missing CSP,
* weak TLS support.

## Medium

Examples:

* weak cookie policies,
* missing Referrer-Policy,
* no DMARC.

## Low

Examples:

* missing security.txt,
* outdated informational headers.

## Informational

Examples:

* framework detection,
* CDN presence.

---

# 18. AI Usage Policy

The platform SHOULD NOT rely on AI for:

* transport analysis,
* header validation,
* deterministic findings,
* scoring,
* fingerprinting,
* dependency lookup.

AI MAY be used for:

* summarization,
* remediation explanations,
* prioritization,
* natural language reporting,
* conversational UX.

The core engine must remain deterministic.

---

# 19. Suggested Service Architecture

## Components

### Crawl Service

Responsible for:

* URL fetching,
* robots handling,
* request scheduling,
* crawl orchestration.

---

### Analysis Service

Responsible for:

* header analysis,
* TLS analysis,
* dependency detection,
* fingerprinting,
* exposure analysis.

---

### Scoring Service

Responsible for:

* severity assignment,
* risk aggregation,
* scoring normalization.

---

### Reporting Service

Responsible for:

* JSON exports,
* Markdown reports,
* PDF rendering,
* audit history.

---

### Scheduler Service

Responsible for:

* recurring audits,
* monitoring mode,
* incremental rescans.

---

# 20. Recommended MVP Scope

## Phase 1 MVP

Implement first:

* TLS analysis,
* security headers,
* cookie analysis,
* robots.txt,
* security.txt,
* DNS security,
* technology detection,
* JS library detection,
* sourcemap detection,
* global security score.

---

# 21. Recommended Future Features

## Possible Expansions

* historical trend analysis,
* organization-wide dashboards,
* multi-domain monitoring,
* GitHub integration,
* CI/CD integration,
* webhook alerts,
* scheduled rescans,
* compliance templates,
* export APIs.

---

# 22. Important Engineering Principles

## Deterministic First

Prefer:

* rules,
* parsers,
* protocols,
* explicit heuristics.

Avoid unnecessary AI usage.

---

## Compliance First

The platform must:

* remain non-invasive,
* remain transparent,
* remain rate-limited,
* remain passive by default.

---

## Explainable Findings

Every finding should contain:

* evidence,
* affected resource,
* severity,
* remediation guidance,
* confidence level.

---

## Safe Defaults

All dangerous functionality should be:

* disabled by default,
* opt-in only,
* strongly restricted.

---

# 23. Out of Scope

The following are intentionally excluded:

* exploit execution,
* SQL injection attacks,
* XSS payload injection,
* brute force,
* credential stuffing,
* authentication bypass,
* aggressive fuzzing,
* privilege escalation,
* malware deployment,
* destructive testing.

The platform is NOT an offensive security framework.

---

# 24. Final Design Philosophy

The project should behave as:

* professional passive auditor,
* safe compliance platform,
* deterministic security analyzer,
* infrastructure hygiene assessment system.

The main value proposition is:

* safe automation,
* passive assessment,
* actionable reporting,
* infrastructure visibility,
* continuous monitoring.
