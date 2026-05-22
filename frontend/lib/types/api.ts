export type Severity = "critical" | "high" | "medium" | "low" | "info" | "informational";
export type AccessibilitySeverity = "critical" | "serious" | "moderate" | "minor";
export type HttpStatus = "ok" | "redirect" | "client_error" | "server_error" | "timeout" | "connection_error";
export type UrlStatus = "allowed" | "blocked_by_robots" | "fetch_error";
export type Grade = "A" | "B" | "C" | "D" | "F";
export type ReportFormat = "json" | "pdf" | "csv";
export type CategoryStatus = "ok" | "error" | "not_included";
export type AuditCheckType = "health" | "seo" | "accessibility" | "security";

export const ALL_AUDIT_CHECKS: AuditCheckType[] = ["health", "seo", "accessibility", "security"];

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

export interface SecurityFinding {
  category: string;
  title: string;
  description: string;
  severity: Severity;
  evidence: string | null;
  affected_resource: string | null;
  remediation: string | null;
}

export interface HeadersResult {
  score: number;
  headers_present: string[];
  headers_missing: string[];
  findings: SecurityFinding[];
}

export interface TlsResult {
  score: number;
  tls_version: string | null;
  certificate_valid: boolean | null;
  certificate_expiry_days: number | null;
  findings: SecurityFinding[];
}

export interface CookieResult {
  score: number;
  total_cookies: number;
  findings: SecurityFinding[];
}

export interface DnsResult {
  score: number;
  spf_present: boolean;
  dmarc_present: boolean;
  dnssec_enabled: boolean;
  caa_present: boolean;
  findings: SecurityFinding[];
}

export interface FrontendSecurityResult {
  score: number;
  technologies_detected: string[];
  findings: SecurityFinding[];
}

export interface DependencyResult {
  score: number;
  js_libraries: string[];
  findings: SecurityFinding[];
}

export interface BestPracticesResult {
  score: number;
  security_txt_present: boolean;
  robots_txt_present: boolean;
  sourcemaps_found: string[];
  findings: SecurityFinding[];
}

export interface SecurityAuditResult {
  url: string;
  overall_score: number;
  headers: HeadersResult;
  tls: TlsResult;
  cookies: CookieResult;
  dns: DnsResult;
  frontend: FrontendSecurityResult;
  dependencies: DependencyResult;
  best_practices: BestPracticesResult;
  all_findings: SecurityFinding[];
  checked_with: string;
}

export interface CategoryResult {
  name: string;
  score: number | null;
  status: CategoryStatus;
  error?: string | null;
}

export interface ScoreBreakdown {
  categories: CategoryResult[];
  overall_score: number | null;
  grade: Grade | null;
}

export interface DiscoveryRequest {
  url: string;
  email: string;
  max_sites?: number | null;
  max_depth?: number | null;
}

export interface AuditRequest {
  url: string;
  email: string;
  report_name?: string | null;
  selected_urls?: string[] | null;
  discovery_result?: DiscoveryResult | null;
  scope?: AuditCheckType[] | null;
  max_sites?: number | null;
  max_depth?: number | null;
  enable_ai_summary?: boolean;
}

export interface PageAuditResult {
  url: string;
  health: HealthCheckResult | null;
  seo: SeoAnalysisResult | null;
  accessibility: AccessibilityResult | null;
  security: SecurityAuditResult | null;
}

export type AiSummaryStatus = "ok" | "error";

export interface AiSummaryOverview {
  overall_assessment: string;
  main_strengths: string[];
  main_weaknesses: string[];
  priority_recommendations: string[];
}

export interface AiPageSummary {
  url: string;
  summary: string;
  recommended_actions: string[];
}

export interface AiSummary {
  status: AiSummaryStatus;
  audit_id: string;
  model: string | null;
  generated_at: string | null;
  summary: AiSummaryOverview | null;
  problematic_pages: AiPageSummary[];
  error: string | null;
}

export interface AuditReport {
  audit_id: string;
  report_name: string;
  root_url: string;
  generated_at: string;
  format: ReportFormat;
  discovery: DiscoveryResult;
  health: HealthCheckResult | null;
  seo: SeoAnalysisResult | null;
  accessibility: AccessibilityResult | null;
  security: SecurityAuditResult | null;
  score_breakdown: ScoreBreakdown;
  page_results: PageAuditResult[];
  scope: AuditCheckType[];
  ai_summary: AiSummary | null;
}

export interface AuditResponse {
  success: boolean;
  report: AuditReport;
}

export interface DiscoveryEvent {
  type: "phase" | "url";
  message: string;
  count?: number | null;
  elapsed_seconds?: number | null;
  max_duration_seconds?: number | null;
}

export interface AuditEvent {
  type: "phase" | "complete";
  message: string;
  elapsed_seconds?: number | null;
  max_duration_seconds?: number | null;
  result?: AuditReport | null;
}

export interface ApiError {
  error: string;
  message: string;
}
