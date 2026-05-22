import type { Severity, AccessibilitySeverity } from "@/lib/types/api";

export type MetricStatus = "good" | "warn" | "bad";

export function scoreStatus(score: number): MetricStatus {
  if (score >= 80) return "good";
  if (score >= 60) return "warn";
  return "bad";
}

export function statusColor(s: MetricStatus): string {
  if (s === "good") return "text-accent";
  if (s === "warn") return "text-warning";
  return "text-destructive";
}

export function statusBar(s: MetricStatus): string {
  if (s === "good") return "bg-accent";
  if (s === "warn") return "bg-warning";
  return "bg-destructive";
}

export function ttfbStatus(ms: number | null): MetricStatus {
  if (ms === null) return "warn";
  if (ms < 800) return "good";
  if (ms < 1800) return "warn";
  return "bad";
}

export function issueSeverityColor(severity: Severity | AccessibilitySeverity): string {
  if (severity === "critical" || severity === "high" || severity === "serious") {
    return "text-destructive bg-destructive/10";
  }
  if (severity === "medium" || severity === "moderate") {
    return "text-warning bg-warning/10";
  }
  return "text-muted-foreground bg-secondary";
}
