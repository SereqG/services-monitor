# Frontend ↔ Backend Integration Guide

## Status

The backend is ready for integration with the following caveats:

| Area | Status | Notes |
|------|--------|-------|
| All endpoints operational | ✅ | Validated, tests passing |
| CORS configured | ✅ | `*` (open) — restrict in production |
| Authentication | ❌ Not yet | Anonymous MVP — add auth in Phase 2 |
| Persistent report storage | ❌ Not yet | Reports returned inline only |
| Async job queue | ❌ Not yet | Audit runs synchronously — expect 15–60s response time |
| PDF export | ❌ Not yet | Phase 2 |

> **Important for frontend:** The `/api/v1/audit` endpoint is synchronous and may take 15–60 seconds depending on the target site. Set a long timeout (90s+), show a visible loading state, and do not retry on timeout without user confirmation.

---

## Base URL

```
http://localhost:8000
```

Start the server:

```bash
cd apps/api
uvicorn main:app --reload
```

Interactive docs: `http://localhost:8000/docs`

---

## Recommended Integration Workflow

The intended UX flow maps to two API calls:

```
Step 1 — POST /api/v1/discovery
         → user reviews discovered URLs, selects scope

Step 2 — POST /api/v1/audit  (with selected_urls from step 1)
         → full report returned inline
```

Steps 2–4 from the architecture doc (validate → discover → select → audit) collapse to these two calls for MVP.

---

## Error Response Format

All validation and processing errors return `HTTP 400`:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description"
}
```

Pydantic validation errors (malformed JSON, wrong types) return `HTTP 422` from FastAPI with the standard detail array.

### Known error codes

| Code | Trigger |
|------|---------|
| `INVALID_SCHEME` | URL is not HTTPS |
| `SUBPAGE_NOT_ALLOWED` | URL has a path (only root URLs accepted) |
| `URL_TOO_LONG` | URL exceeds 200 characters |
| `INVALID_URL` | URL has no valid domain |
| `SSRF_LOCALHOST` | URL resolves to localhost |
| `SSRF_PRIVATE_IP` | URL resolves to a private/internal IP |

---

## Endpoints

---

### `POST /api/v1/validate`

Validates user input before running discovery. Use this for inline form validation before the user submits.

**Request body**

```json
{
  "url": "https://example.com",
  "email": "user@example.com",
  "report_name": "My Audit"
}
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `url` | string | yes | Must be HTTPS, root only (no path), max 200 chars, no private IPs |
| `email` | string (email) | yes | Valid email format, max 200 chars |
| `report_name` | string \| null | no | Max 200 chars; special characters stripped automatically |

**Response `200`**

```json
{
  "url": "https://example.com",
  "email": "user@example.com",
  "report_name": "My Audit",
  "is_valid": true,
  "errors": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Validated URL (unchanged) |
| `email` | string | Validated email |
| `report_name` | string \| null | Sanitized report name |
| `is_valid` | boolean | Always `true` on 200 — errors raise 400 |
| `errors` | string[] | Always `[]` on 200 |

**Error `400`**

```json
{
  "error": "INVALID_SCHEME",
  "message": "URL must use HTTPS scheme"
}
```

---

### `POST /api/v1/discovery`

Runs the discovery crawl: fetches `robots.txt`, detects sitemap, and BFS-crawls the site up to the hard caps. Returns the discovered URL structure so the frontend can render a selection UI.

**Hard caps (server-side, not configurable by client)**

| Limit | Value |
|-------|-------|
| Max URLs discovered | 500 |
| Max crawl depth | 3 |
| Max duration | 120 seconds |
| Max HTTP requests | 1000 |

**Request body**

```json
{
  "url": "https://example.com",
  "email": "user@example.com",
  "report_name": "My Audit"
}
```

Same fields as `/api/v1/validate`. `email` and `report_name` are accepted for consistency but not used during discovery.

**Response `200`**

```json
{
  "root_url": "https://example.com",
  "robots_policy": {
    "fetched": true,
    "allows_root": true,
    "blocked_paths": ["/admin", "/private"],
    "sitemap_urls": ["https://example.com/sitemap.xml"],
    "raw": "User-agent: *\nDisallow: /admin\n..."
  },
  "discovered_urls": [
    {
      "url": "https://example.com/",
      "depth": 0,
      "status": "allowed"
    },
    {
      "url": "https://example.com/blog",
      "depth": 1,
      "status": "allowed"
    },
    {
      "url": "https://example.com/admin",
      "depth": 1,
      "status": "blocked_by_robots"
    }
  ],
  "total_discovered": 3,
  "total_allowed": 2,
  "hit_limit": false,
  "duration_seconds": 4.21
}
```

**`robots_policy` object**

| Field | Type | Description |
|-------|------|-------------|
| `fetched` | boolean | Whether `robots.txt` was successfully fetched |
| `allows_root` | boolean | Whether `/` is allowed for crawling |
| `blocked_paths` | string[] | Paths disallowed for `*` or `ServiceMonitorBot` |
| `sitemap_urls` | string[] | Sitemap URLs found in `robots.txt` |
| `raw` | string \| null | Raw `robots.txt` content |

**`discovered_urls[]` item**

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Absolute URL |
| `depth` | integer | Crawl depth (0 = root) |
| `status` | `"allowed"` \| `"blocked_by_robots"` | Whether the URL can be audited |

**Top-level fields**

| Field | Type | Description |
|-------|------|-------------|
| `root_url` | string | The input URL |
| `total_discovered` | integer | Total URLs found (allowed + blocked) |
| `total_allowed` | integer | URLs available for selection |
| `hit_limit` | boolean | `true` if any hard cap was reached |
| `duration_seconds` | float | Wall-clock time of the crawl |

> **Frontend note:** Only render URLs with `status === "allowed"` in the selection UI. URLs with `status === "blocked_by_robots"` may be shown as disabled/greyed out for transparency.

---

### `POST /api/v1/health-check`

Checks the HTTP health of a single URL. Useful for a quick availability indicator before running a full audit.

**Request body**

```json
{
  "url": "https://example.com"
}
```

| Field | Type | Required |
|-------|------|----------|
| `url` | string | yes |

**Response `200`**

```json
{
  "url": "https://example.com",
  "final_url": "https://www.example.com/",
  "status_code": 200,
  "status": "ok",
  "ttfb_ms": 312.4,
  "redirect_chain": [
    {
      "url": "https://example.com",
      "status_code": 301
    }
  ],
  "has_redirect_loop": false,
  "is_available": true,
  "error": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Original requested URL |
| `final_url` | string | URL after all redirects |
| `status_code` | integer \| null | Final HTTP status code; `null` on timeout/connection error |
| `status` | string | Classified status (see table below) |
| `ttfb_ms` | float \| null | Time to first byte in milliseconds |
| `redirect_chain` | object[] | Each redirect hop with its URL and status code |
| `has_redirect_loop` | boolean | `true` if a redirect loop was detected |
| `is_available` | boolean | `true` if `status_code < 400` |
| `error` | string \| null | Error message on timeout or connection failure |

**`status` values**

| Value | Meaning |
|-------|---------|
| `ok` | 2xx response |
| `redirect` | 3xx response (without following) |
| `client_error` | 4xx |
| `server_error` | 5xx |
| `timeout` | Request timed out |
| `connection_error` | Could not connect |

---

### `POST /api/v1/seo`

Runs SEO analysis on a single URL. Returns meta data, heading structure, issues with severity, and a 0–100 score.

**Request body**

```json
{
  "url": "https://example.com"
}
```

**Response `200`**

```json
{
  "url": "https://example.com",
  "meta": {
    "title": "Example Domain",
    "title_length": 14,
    "description": "This domain is for use in illustrative examples.",
    "description_length": 48,
    "canonical": "https://example.com/",
    "robots_meta": null,
    "og_title": null,
    "og_description": null,
    "og_image": null
  },
  "headings": {
    "h1_count": 1,
    "h2_count": 3,
    "h3_count": 5,
    "h1_texts": ["Example Domain"]
  },
  "has_sitemap": false,
  "has_schema_markup": false,
  "images_without_alt": 0,
  "issues": [
    {
      "code": "TITLE_TOO_SHORT",
      "severity": "medium",
      "message": "Title too short (14 chars, min 30)",
      "detail": null
    },
    {
      "code": "DESC_TOO_SHORT",
      "severity": "medium",
      "message": "Meta description too short (48 chars, min 120)"
    },
    {
      "code": "MISSING_CANONICAL",
      "severity": "medium",
      "message": "Canonical tag is missing"
    }
  ],
  "score": 76
}
```

**`meta` object**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string \| null | Page `<title>` text |
| `title_length` | integer \| null | Character count |
| `description` | string \| null | `<meta name="description">` content |
| `description_length` | integer \| null | Character count |
| `canonical` | string \| null | `<link rel="canonical">` href |
| `robots_meta` | string \| null | `<meta name="robots">` content |
| `og_title` | string \| null | `og:title` |
| `og_description` | string \| null | `og:description` |
| `og_image` | string \| null | `og:image` |

**`headings` object**

| Field | Type | Description |
|-------|------|-------------|
| `h1_count` | integer | Number of `<h1>` elements |
| `h2_count` | integer | Number of `<h2>` elements |
| `h3_count` | integer | Number of `<h3>` elements |
| `h1_texts` | string[] | Text content of each `<h1>` |

**`issues[]` item**

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Machine-readable issue identifier |
| `severity` | `"critical"` \| `"high"` \| `"medium"` \| `"low"` \| `"info"` | Severity level |
| `message` | string | Human-readable description |
| `detail` | string \| null | Optional extra context |

**Known issue codes**

| Code | Severity | Trigger |
|------|----------|---------|
| `MISSING_TITLE` | critical | No `<title>` tag |
| `TITLE_TOO_SHORT` | medium | Title < 30 chars |
| `TITLE_TOO_LONG` | low | Title > 60 chars |
| `MISSING_DESCRIPTION` | high | No meta description |
| `DESC_TOO_SHORT` | medium | Description < 120 chars |
| `DESC_TOO_LONG` | low | Description > 160 chars |
| `MISSING_H1` | high | No `<h1>` element |
| `MULTIPLE_H1` | medium | More than one `<h1>` |
| `MISSING_CANONICAL` | medium | No canonical tag |
| `IMAGES_MISSING_ALT` | medium | One or more `<img>` without `alt` |

---

### `POST /api/v1/audit`

Runs the full audit pipeline: validates input → discovery crawl → health check → SEO analysis → accessibility analysis → score calculation. Returns a complete `AuditReport`.

> **Expect 15–60 seconds response time.** Use a long timeout and show a loading state.

**Request body**

```json
{
  "url": "https://example.com",
  "email": "user@example.com",
  "report_name": "Q2 Audit",
  "selected_urls": [
    "https://example.com/",
    "https://example.com/about",
    "https://example.com/blog"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | yes | Root HTTPS URL, no path |
| `email` | string | yes | Contact email for the report |
| `report_name` | string \| null | no | Display name for the report; auto-sanitized |
| `selected_urls` | string[] \| null | no | URLs chosen from the discovery step; if omitted, the audit runs on the root only |

**Response `200`**

```json
{
  "success": true,
  "report": {
    "report_name": "Q2 Audit",
    "root_url": "https://example.com",
    "generated_at": "2026-05-19T10:30:00.000000+00:00",
    "format": "json",
    "discovery": { ... },
    "health": { ... },
    "seo": { ... },
    "accessibility": { ... },
    "score_breakdown": { ... }
  }
}
```

**`report` object**

| Field | Type | Description |
|-------|------|-------------|
| `report_name` | string | Name provided in request or falls back to the URL |
| `root_url` | string | Audited URL |
| `generated_at` | string (ISO 8601) | UTC timestamp of report generation |
| `format` | `"json"` \| `"pdf"` \| `"csv"` | Always `"json"` in MVP |
| `discovery` | object | Full `DiscoveryResult` — see `/api/v1/discovery` response |
| `health` | object | Full `HealthCheckResult` — see `/api/v1/health-check` response |
| `seo` | object | Full `SeoAnalysisResult` — see `/api/v1/seo` response |
| `accessibility` | object | See `accessibility` schema below |
| `score_breakdown` | object | See `score_breakdown` schema below |

**`accessibility` object**

```json
{
  "url": "https://example.com",
  "issues": [
    {
      "code": "MISSING_LANG_ATTR",
      "severity": "serious",
      "message": "<html> element is missing lang attribute",
      "element": null,
      "count": 1
    }
  ],
  "score": 85,
  "checked_with": "html-heuristics",
  "note": "Full audit requires browser-based axe-core integration (Phase 2)"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Audited URL |
| `issues` | object[] | Detected accessibility issues |
| `score` | integer | 0–100 |
| `checked_with` | string | Engine used (`"html-heuristics"` in MVP) |
| `note` | string \| null | Limitations disclaimer |

**Accessibility issue `code` values**

| Code | Severity | Trigger |
|------|----------|---------|
| `IMG_MISSING_ALT` | serious | `<img>` without `alt` attribute |
| `INPUT_MISSING_LABEL` | serious | `<input>` without label or `aria-label` |
| `MISSING_MAIN_LANDMARK` | moderate | No `<main>` or `role="main"` |
| `MISSING_LANG_ATTR` | serious | `<html>` without `lang` attribute |

**`score_breakdown` object**

```json
{
  "categories": [
    { "name": "performance", "weight": 0.30, "raw_score": 50, "weighted_score": 15.0 },
    { "name": "seo",         "weight": 0.30, "raw_score": 76, "weighted_score": 22.8 },
    { "name": "accessibility","weight": 0.20, "raw_score": 85, "weighted_score": 17.0 },
    { "name": "health",      "weight": 0.15, "raw_score": 100, "weighted_score": 15.0 },
    { "name": "security",    "weight": 0.05, "raw_score": 50, "weighted_score": 2.5 }
  ],
  "overall_score": 72,
  "grade": "B"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `categories` | object[] | One entry per scoring category |
| `overall_score` | integer | 0–100 weighted average |
| `grade` | `"A"` \| `"B"` \| `"C"` \| `"D"` \| `"F"` | Letter grade |

**Category `weight` values (fixed, transparent)**

| Category | Weight | Source |
|----------|--------|--------|
| `performance` | 30% | Placeholder (50) until Lighthouse — Phase 2 |
| `seo` | 30% | From `/api/v1/seo` |
| `accessibility` | 20% | From accessibility heuristics |
| `health` | 15% | From `/api/v1/health-check` |
| `security` | 5% | Placeholder (50) until security engine — Phase 2 |

**Grade thresholds**

| Grade | Score range |
|-------|-------------|
| A | 90–100 |
| B | 75–89 |
| C | 60–74 |
| D | 40–59 |
| F | 0–39 |

---

## TypeScript Types

Copy these into `apps/web/src/types/api.ts` (or your contracts package):

```typescript
// Shared
export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type AccessibilitySeverity = "critical" | "serious" | "moderate" | "minor";
export type HttpStatus = "ok" | "redirect" | "client_error" | "server_error" | "timeout" | "connection_error";
export type UrlStatus = "allowed" | "blocked_by_robots";
export type Grade = "A" | "B" | "C" | "D" | "F";
export type ReportFormat = "json" | "pdf" | "csv";

// Validation
export interface AuditInput {
  url: string;
  email: string;
  report_name?: string | null;
}

export interface ValidationResult {
  url: string;
  email: string;
  report_name: string | null;
  is_valid: boolean;
  errors: string[];
}

// Discovery
export interface RobotsPolicy {
  fetched: boolean;
  allows_root: boolean;
  blocked_paths: string[];
  sitemap_urls: string[];
  raw: string | null;
}

export interface DiscoveredUrl {
  url: string;
  depth: number;
  status: UrlStatus;
}

export interface DiscoveryResult {
  root_url: string;
  robots_policy: RobotsPolicy;
  discovered_urls: DiscoveredUrl[];
  total_discovered: number;
  total_allowed: number;
  hit_limit: boolean;
  duration_seconds: number;
}

// Health check
export interface RedirectHop {
  url: string;
  status_code: number;
}

export interface HealthCheckResult {
  url: string;
  final_url: string;
  status_code: number | null;
  status: HttpStatus;
  ttfb_ms: number | null;
  redirect_chain: RedirectHop[];
  has_redirect_loop: boolean;
  is_available: boolean;
  error: string | null;
}

// SEO
export interface MetaData {
  title: string | null;
  title_length: number | null;
  description: string | null;
  description_length: number | null;
  canonical: string | null;
  robots_meta: string | null;
  og_title: string | null;
  og_description: string | null;
  og_image: string | null;
}

export interface HeadingStructure {
  h1_count: number;
  h2_count: number;
  h3_count: number;
  h1_texts: string[];
}

export interface SeoIssue {
  code: string;
  severity: Severity;
  message: string;
  detail: string | null;
}

export interface SeoAnalysisResult {
  url: string;
  meta: MetaData;
  headings: HeadingStructure;
  has_sitemap: boolean;
  has_schema_markup: boolean;
  images_without_alt: number;
  issues: SeoIssue[];
  score: number;
}

// Accessibility
export interface AccessibilityIssue {
  code: string;
  severity: AccessibilitySeverity;
  message: string;
  element: string | null;
  count: number;
}

export interface AccessibilityResult {
  url: string;
  issues: AccessibilityIssue[];
  score: number;
  checked_with: string;
  note: string | null;
}

// Scoring
export interface CategoryScore {
  name: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
}

export interface ScoreBreakdown {
  categories: CategoryScore[];
  overall_score: number;
  grade: Grade;
}

// Audit
export interface AuditRequest {
  url: string;
  email: string;
  report_name?: string | null;
  selected_urls?: string[] | null;
}

export interface AuditReport {
  report_name: string;
  root_url: string;
  generated_at: string;
  format: ReportFormat;
  discovery: DiscoveryResult;
  health: HealthCheckResult;
  seo: SeoAnalysisResult;
  accessibility: AccessibilityResult;
  score_breakdown: ScoreBreakdown;
}

export interface AuditResponse {
  success: boolean;
  report: AuditReport;
}

// Error
export interface ApiError {
  error: string;
  message: string;
}
```

---

## Example API Calls (fetch)

### Step 1 — Run discovery

```typescript
const response = await fetch("http://localhost:8000/api/v1/discovery", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ url: "https://example.com", email: "user@example.com" }),
});

if (!response.ok) {
  const error: ApiError = await response.json();
  // handle error.code / error.message
}

const discovery: DiscoveryResult = await response.json();
const selectableUrls = discovery.discovered_urls.filter(u => u.status === "allowed");
```

### Step 2 — Run full audit

```typescript
const response = await fetch("http://localhost:8000/api/v1/audit", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  signal: AbortSignal.timeout(90_000), // 90s timeout
  body: JSON.stringify({
    url: "https://example.com",
    email: "user@example.com",
    report_name: "My Audit",
    selected_urls: ["https://example.com/", "https://example.com/about"],
  }),
});

if (!response.ok) {
  const error: ApiError = await response.json();
  // handle
}

const { report }: AuditResponse = await response.json();
```

---

## Environment Variable (frontend)

Add to `apps/web/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Use in fetch calls:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;
fetch(`${API_URL}/api/v1/audit`, ...);
```

---

## Known Limitations (MVP)

| Limitation | Impact | Planned fix |
|-----------|--------|-------------|
| Synchronous audit execution | 15–60s blocking request | Async job queue in Phase 2 |
| No report storage | Reports are not saved — refreshing loses data | DB persistence in Phase 2 |
| `performance` score is a placeholder (50) | Score is understated | Lighthouse integration in Phase 2 |
| `security` score is a placeholder (50) | Score is understated | Security engine in Phase 2 |
| Accessibility uses HTML heuristics only | Misses JS-rendered issues | axe-core / Playwright in Phase 2 |
| No authentication | Anyone can trigger audits | Auth layer in Phase 2 |
