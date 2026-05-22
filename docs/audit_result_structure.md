# Audit Result Structure — Technical Reference

## Purpose

This document explains the complete structure of the data produced by the audit pipeline: what every field means, where it comes from, and how the pieces relate to each other. It is the authoritative reference for anyone building features on top of audit output (reporting, frontend, exports, comparisons).

---

## Entry Points

The audit produces one of two output shapes depending on how it is invoked:

| Entry point | Schema | When used |
|---|---|---|
| `run_audit()` | `AuditResponse { success, report: AuditReport }` | Single-call, returns when complete |
| `stream_audit()` | `AsyncGenerator[AuditEvent, ...]` | SSE stream; last event carries `result: AuditReport` |

Both eventually deliver the same `AuditReport` object.

---

## Top-Level: `AuditReport`

Defined in `slices/reporting/schemas.py`. This is the root of all audit output.

```
AuditReport
├── audit_id: str                 (uuid4 hex, generated per audit run)
├── report_name: str
├── root_url: str
├── generated_at: str             (ISO 8601 timestamp)
├── scope: list[str]              (checks that ran, e.g. ["health", "seo", "security"])
├── format: ReportFormat          (json | pdf | csv, default: json)
│
├── discovery: DiscoveryResult    (always present)
├── health: HealthCheckResult?    (null if "health" not in scope)
├── seo: SeoAnalysisResult?       (null if "seo" not in scope)
├── accessibility: AccessibilityResult?   (null if "accessibility" not in scope)
├── security: SecurityAuditResult?        (null if "security" not in scope or errored)
│
├── score_breakdown: ScoreBreakdown
├── page_results: list[PageAuditResult]
└── ai_summary: AiSummary?        (null unless AI summary was requested)
```

**`audit_id`** — a `uuid4().hex` string generated at the start of every audit run. Used to key the AI context dataset stored at `storage/ai_context/{audit_id}.json`.

**`report_name`** — taken from `AuditRequest.report_name`; falls back to the root URL if not provided.

**`scope`** — sorted list of check names that were actually executed. Determined by `AuditRequest.scope`; defaults to all four checks (`health`, `seo`, `accessibility`, `security`) when not specified.

**`format`** — reserved for export format selection; does not affect the JSON structure of the report itself.

**`ai_summary`** — the optional AI explanation layer. `null` unless `AuditRequest.enable_ai_summary` is `true`. AI summary is **non-critical**: if generation fails (or the server has no API key), the field carries `status="error"` with an explicit message rather than failing the audit. AI output is purely explanatory — it never affects scores, grades, or any deterministic result. See section 8 and `docs/ai_audit_summary_architecture_claude_prompt.md`.

---

## Data Flow

```
AuditRequest.url
    │
    ▼
validate_url()                     → normalized root URL
    │
    ▼
run_discovery()                    → DiscoveryResult  (sequential, always first)
    │
    ▼
asyncio.gather(                    → all checks run concurrently
    check_health()                 → HealthCheckResult
    analyze_seo()                  → SeoAnalysisResult
    analyze_accessibility()        → AccessibilityResult
    check_security()               → SecurityAuditResult  (errors caught, not raised)
)
    │
    ▼
CategoryResult[] assembled         → one entry per category, score extracted
    │
    ▼
calculate_score()                  → ScoreBreakdown
    │
    ▼
assemble_report()                  → AuditReport
```

---

## 1. `DiscoveryResult`

**Source:** `slices/discovery/service.py → run_discovery()`
**Always present.** Runs before all other checks. Maps the site structure and respects `robots.txt`.

```
DiscoveryResult
├── root_url: str
├── robots_policy: RobotsPolicy
│   ├── fetched: bool               (false if robots.txt was unreachable)
│   ├── allows_root: bool
│   ├── blocked_paths: list[str]    (paths disallowed by robots.txt)
│   ├── sitemap_urls: list[str]     (Sitemap: entries from robots.txt)
│   └── raw: str?                   (raw robots.txt content, null if not fetched)
├── discovered_urls: list[DiscoveredUrl]
│   └── DiscoveredUrl
│       ├── url: str
│       ├── depth: int              (0 = root, 1 = one link away, etc.)
│       └── status: allowed | blocked_by_robots
├── total_discovered: int           (all found URLs, including blocked ones)
├── total_allowed: int              (only URLs with status=allowed)
├── hit_limit: bool                 (true if max_sites or max_depth cap was reached)
└── duration_seconds: float
```

`hit_limit=true` means the crawl was stopped by a configured limit, not because no more pages exist. The consumer should treat discovery as potentially incomplete in that case.

---

## 2. `HealthCheckResult`

**Source:** `slices/health_check/service.py → check_health()`
**Scope key:** `"health"`

Measures reachability, response time, and redirect behavior for a single URL. Called once for the root URL (stored in `AuditReport.health`) and once per subpage (stored in `PageAuditResult.health`).

```
HealthCheckResult
├── url: str                        (the URL that was requested)
├── final_url: str                  (URL after all redirects have been followed)
├── status_code: int?               (null on timeout or connection error)
├── status: HttpStatus
│   └── ok | redirect | client_error | server_error | timeout | connection_error
├── ttfb_ms: float?                 (time to first byte in ms; null if request failed)
├── redirect_chain: list[RedirectHop]
│   └── RedirectHop
│       ├── url: str                (origin of this redirect hop)
│       └── status_code: int       (the 3xx code that caused the next hop)
├── has_redirect_loop: bool
├── is_available: bool              (true only when status_code < 400)
└── error: str?                     (human-readable, set on timeout or connection error)
```

### How `redirect_chain` works

httpx follows redirects automatically. After the final response arrives, every intermediate response is recorded in `response.history`. The service walks that list and builds `redirect_chain` from it.

Example: `http://example.com` → 301 → `http://www.example.com` → 302 → `https://www.example.com` → 200

```
redirect_chain = [
    RedirectHop(url="http://example.com",     status_code=301),
    RedirectHop(url="http://www.example.com", status_code=302),
]
final_url    = "https://www.example.com"
status_code  = 200
```

Each hop is the **origin** of the redirect, not the destination. The final URL (200 OK) is `final_url`, not in the chain.

### How `has_redirect_loop` is detected

The service collects all intermediate URLs into a `seen_urls` set as it builds the chain. After the final response, it checks whether `final_url` is already in `seen_urls`. If it is, the server redirected back to a URL that was already visited — a loop.

### How `ttfb_ms` drives performance scoring

`ttfb_ms` is used in `run_audit()` to produce the `performance` category in `ScoreBreakdown`:

| TTFB | Score |
|---|---|
| < 200 ms | 100 |
| < 500 ms | 80 |
| < 800 ms | 60 |
| < 1500 ms | 40 |
| ≥ 1500 ms | 20 |

If `ttfb_ms` is null (request failed), the `performance` category gets `status=error` and no score — it is excluded from the overall average.

---

## 3. `SeoAnalysisResult`

**Source:** `slices/seo/service.py → analyze_seo()`
**Scope key:** `"seo"`

```
SeoAnalysisResult
├── url: str
├── meta: MetaData
│   ├── title: str?
│   ├── title_length: int?
│   ├── description: str?
│   ├── description_length: int?
│   ├── canonical: str?
│   ├── robots_meta: str?           (content of <meta name="robots">)
│   ├── og_title: str?
│   ├── og_description: str?
│   └── og_image: str?
├── headings: HeadingStructure
│   ├── h1_count: int
│   ├── h2_count: int
│   ├── h3_count: int
│   └── h1_texts: list[str]
├── has_sitemap: bool
├── has_schema_markup: bool
├── images_without_alt: int
├── issues: list[SeoIssue]
│   └── SeoIssue
│       ├── code: str               (machine-readable identifier)
│       ├── severity: str           (critical | high | medium | low | info)
│       ├── message: str
│       └── detail: str?
└── score: int                      (0–100; carried directly into ScoreBreakdown)
```

---

## 4. `AccessibilityResult`

**Source:** `slices/accessibility/service.py → analyze_accessibility()`
**Scope key:** `"accessibility"`

```
AccessibilityResult
├── url: str
├── issues: list[AccessibilityIssue]
│   └── AccessibilityIssue
│       ├── code: str
│       ├── severity: str           (critical | serious | moderate | minor)
│       ├── message: str
│       ├── element: str?           (HTML snippet of the offending element)
│       └── count: int              (how many times this issue appears; default 1)
├── score: int                      (0–100; carried directly into ScoreBreakdown)
├── checked_with: str               (e.g. "html-heuristics")
└── note: str?                      (optional disclaimer or context)
```

---

## 5. `SecurityAuditResult`

**Source:** `slices/security/service.py → check_security()`
**Scope key:** `"security"`

The most complex result. Seven sub-analyzers run and each produces its own typed result. The `overall_score` is a weighted average across all seven.

```
SecurityAuditResult
├── url: str
├── overall_score: int              (weighted average; see weights below)
│
├── headers: HeadersResult          (weight: 20)
│   ├── score: int
│   ├── headers_present: list[str]
│   ├── headers_missing: list[str]
│   └── findings: list[SecurityFinding]
│
├── tls: TlsResult                  (weight: 20)
│   ├── score: int
│   ├── tls_version: str?
│   ├── certificate_valid: bool?
│   ├── certificate_expiry_days: int?
│   └── findings: list[SecurityFinding]
│
├── cookies: CookieResult           (weight: 10)
│   ├── score: int
│   ├── total_cookies: int
│   └── findings: list[SecurityFinding]
│
├── dns: DnsResult                  (weight: 10)
│   ├── score: int
│   ├── spf_present: bool
│   ├── dmarc_present: bool
│   ├── dnssec_enabled: bool
│   ├── caa_present: bool
│   └── findings: list[SecurityFinding]
│
├── frontend: FrontendResult        (weight: 15)
│   ├── score: int
│   ├── technologies_detected: list[str]
│   └── findings: list[SecurityFinding]
│
├── dependencies: DependencyResult  (weight: 15)
│   ├── score: int
│   ├── js_libraries: list[str]
│   └── findings: list[SecurityFinding]
│
├── best_practices: BestPracticesResult  (weight: 10)
│   ├── score: int
│   ├── security_txt_present: bool
│   ├── robots_txt_present: bool
│   ├── sourcemaps_found: list[str]
│   └── findings: list[SecurityFinding]
│
├── all_findings: list[SecurityFinding]  (flat union of all sub-analyzer findings)
└── checked_with: str               ("security-audit")
```

### Score weights

Defined in `slices/security/schemas.py → SCORE_WEIGHTS`. Sum is always 100.

| Analyzer | Weight |
|---|---|
| tls | 20 |
| headers | 20 |
| frontend | 15 |
| dependencies | 15 |
| cookies | 10 |
| dns | 10 |
| best_practices | 10 |

### `SecurityFinding`

Shared by all sub-analyzers. Every finding is fully self-describing.

```
SecurityFinding
├── category: str                   (sub-analyzer name, e.g. "tls", "headers")
├── title: str
├── description: str
├── severity: Severity              (critical | high | medium | low | informational)
├── evidence: str?                  (raw data that triggered the finding)
├── affected_resource: str?         (URL, header name, cookie name, etc.)
└── remediation: str?               (what to fix)
```

### Security error handling

Security is the only check whose errors are caught and converted to a `CategoryResult` with `status=error` rather than crashing the entire audit. This is done in `run_audit()` via `_safe_check_security()`. When security errors, `AuditReport.security` is `null` and the security category is excluded from the overall score average.

---

## 6. `ScoreBreakdown`

**Source:** `slices/scoring/service.py → calculate_score()`
**Built from:** category results assembled in `run_audit()` / `stream_audit()`

```
ScoreBreakdown
├── categories: list[CategoryResult]
│   └── CategoryResult
│       ├── name: str
│       ├── score: int?             (null when status != ok)
│       ├── status: CategoryStatus  (ok | error | not_included)
│       └── error: str?             (set only when status=error)
├── overall_score: int?             (null if no category has status=ok)
└── grade: str?                     (null if overall_score is null)
```

### Categories and their score sources

| Category name | Score source | Status when missing |
|---|---|---|
| `health` | 100 if `is_available`, 0 otherwise; −30 if redirect loop | `not_included` |
| `performance` | Tiered from `ttfb_ms` (see table in section 2) | `error` if `ttfb_ms` is null; `not_included` if health not in scope |
| `seo` | `SeoAnalysisResult.score` | `not_included` |
| `accessibility` | `AccessibilityResult.score` | `not_included` |
| `security` | `SecurityAuditResult.overall_score` | `error` if check threw; `not_included` if not in scope |

### `overall_score` calculation

Simple average of all categories with `status=ok`. Categories with `status=error` or `status=not_included` are completely excluded — they do not drag the average down, and they do not count as zero.

```python
ok_scores = [c.score for c in categories if c.status == CategoryStatus.ok]
overall   = round(sum(ok_scores) / len(ok_scores)) if ok_scores else None
```

### Grade thresholds

| Score | Grade |
|---|---|
| ≥ 90 | A |
| ≥ 75 | B |
| ≥ 60 | C |
| ≥ 40 | D |
| < 40 | F |

---

## 7. `PageAuditResult`

**Source:** assembled in `run_audit()` / `stream_audit()`

Holds per-page results for the root URL and any selected subpages. Security runs per-page via `_audit_page()` using `_safe_check_security()`. If security errors on a subpage it is caught and `security` is `null` for that page without failing the audit.

```
PageAuditResult
├── url: str
├── health: HealthCheckResult?
├── seo: SeoAnalysisResult?
├── accessibility: AccessibilityResult?
└── security: SecurityAuditResult?
```

### How `page_results` is populated

1. The first entry is always the root URL, using the results already collected for `AuditReport.health`, `.seo`, and `.accessibility`.
2. Additional entries are added only if `AuditRequest.selected_urls` is provided.
3. Each URL in `selected_urls` is validated against the discovery result — it must appear with `status=allowed`. URLs that are blocked by robots.txt or were not discovered are silently skipped.
4. Subpages run `check_health`, `analyze_seo`, and `analyze_accessibility` concurrently via `asyncio.gather`.

---

## 8. `AiSummary`

Defined in `slices/ai_summary/schemas.py`. The optional AI explanation layer attached to `AuditReport.ai_summary`. `null` unless `AuditRequest.enable_ai_summary` is `true`.

```
AiSummary
├── status: "ok" | "error"
├── audit_id: str
├── model: str?                   (LLM model id, e.g. "google/gemini-2.5-flash")
├── generated_at: str?            (ISO 8601 timestamp)
├── summary: AiSummaryOverview?   (present when status=ok)
│   ├── overall_assessment: str
│   ├── main_strengths: list[str]
│   ├── main_weaknesses: list[str]
│   └── priority_recommendations: list[str]
├── problematic_pages: list[AiPageSummary]   (per-page analysis of the weakest pages)
│   └── { url, summary, recommended_actions: list[str] }
└── error: str?                   (human-readable reason, set only when status=error)
```

### How the AI summary is produced

1. The deterministic audit completes and produces a normal `AuditReport`.
2. `slices/ai_summary/preprocessing.py` reduces the report to a small curated `AiAnalysisDataset` (category averages, a consistency metric, common issues, ranked problematic pages). The raw `AuditReport` is **never** sent to the LLM.
3. The dataset is written to `storage/ai_context/{audit_id}.json`.
4. Two LLM completions run via OpenRouter, each with tool access to a deterministic `audit_context_tool` that reads the stored dataset (`general_info` / `per_page_info` modes).
5. The validated result is attached as `AuditReport.ai_summary`.

### Failure semantics

AI is **non-critical**. If the LLM call fails, times out, returns invalid JSON, or no `OPENROUTER_API_KEY` is configured, `ai_summary` carries `status="error"` with an explicit `error` message — the audit itself always succeeds with full deterministic results. AI output never influences scores, grades, or category results.

---

## Null safety rules

The following fields are always non-null regardless of scope or errors:

- `AuditReport.audit_id`
- `AuditReport.discovery`
- `AuditReport.score_breakdown`
- `AuditReport.page_results` (at minimum contains the root URL entry)
- `AuditReport.scope`
- `AuditReport.root_url`, `report_name`, `generated_at`, `format`

Everything else (`health`, `seo`, `accessibility`, `security`, `ai_summary`) may be null when the corresponding check is not in scope, failed, or was not requested.

A `CategoryResult` with `status=not_included` means the check was intentionally skipped. A `CategoryResult` with `status=error` means the check was attempted but failed. Both cases produce `score=null` and are excluded from the overall average.
