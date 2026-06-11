"use client";

import { useState } from "react";
import type {
  PageAuditResult,
  SecurityFinding,
  SeoIssue,
  AccessibilityIssue,
  Severity,
  AccessibilitySeverity,
} from "@/lib/types/api";
import {
  scoreStatus,
  statusColor,
  ttfbStatus,
  issueSeverityColor,
} from "@/lib/utils/scoring";
import { ScoreRing } from "@/components/ui/ScoreRing";
import { useI18n, localizeSeoMessage, localizeA11yMessage, localizeFinding } from "@/lib/i18n";

function computePageScore(page: PageAuditResult): number | null {
  const scores: number[] = [];
  if (page.health !== null) scores.push(page.health.is_available ? 100 : 0);
  if (page.seo !== null) scores.push(page.seo.score);
  if (page.accessibility !== null) scores.push(page.accessibility.score);
  if (page.security !== null) scores.push(page.security.overall_score);
  if (scores.length === 0) return null;
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
}

function MetricChip({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: string;
  colorClass: string;
}) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className={`font-mono text-base font-bold ${colorClass}`}>{value}</span>
      <span className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
    </div>
  );
}

function IssueRow({
  severity,
  source,
  message,
  code,
}: {
  severity: string;
  source: string;
  message: string;
  code: string;
}) {
  const { dict } = useI18n();
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-background p-3">
      <div className="flex shrink-0 flex-col items-center gap-1 pt-0.5">
        <span
          className={`rounded px-1.5 py-0.5 font-mono text-[9px] uppercase ${issueSeverityColor(severity as Severity | AccessibilitySeverity)}`}
        >
          {dict.severity[severity] ?? severity}
        </span>
        <span className="font-mono text-[9px] text-muted-foreground">{source}</span>
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium">{message}</p>
        <p className="font-mono text-[10px] text-muted-foreground">{code}</p>
      </div>
    </div>
  );
}

function IssueSection({
  title,
  issues,
}: {
  title: string;
  issues: Array<{ severity: string; source: string; message: string; code: string }>;
}) {
  const { dict } = useI18n();
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {title}
        </span>
        <span
          className={`font-mono text-[10px] ${issues.length > 0 ? "text-warning" : "text-accent"}`}
        >
          {issues.length > 0 ? dict.pageResult.issues(issues.length) : dict.pageResult.noIssues}
        </span>
      </div>
      {issues.length > 0 && (
        <div className="space-y-2">
          {issues.map((issue, i) => (
            <IssueRow key={i} {...issue} />
          ))}
        </div>
      )}
    </div>
  );
}

export function PageResultCard({ page }: { page: PageAuditResult }) {
  const { lang, dict } = useI18n();
  const [expanded, setExpanded] = useState(false);
  const { security } = page;

  const totalIssues =
    (page.seo?.issues.length ?? 0) +
    (page.accessibility?.issues.length ?? 0) +
    (security?.all_findings.length ?? 0);

  const ttfbMs = page.health?.ttfb_ms ?? null;
  const ttfbLabel = ttfbMs === null ? "—" : `${ttfbMs.toFixed(0)}ms`;
  const ttfbColor = statusColor(ttfbStatus(ttfbMs));

  const httpStatus = page.health?.status_code ?? null;
  const httpLabel = httpStatus !== null ? String(httpStatus) : "—";
  const httpColor = page.health
    ? page.health.is_available
      ? "text-accent"
      : "text-destructive"
    : "text-muted-foreground";

  const shortUrl = page.url.replace(/^https?:\/\//, "").replace(/\/$/, "");

  const pageScore = computePageScore(page);
  const pageStatus = pageScore !== null ? scoreStatus(pageScore) : "bad";

  const seoIssues = (page.seo?.issues ?? []).map((i: SeoIssue) => ({
    severity: i.severity,
    source: "SEO",
    message: localizeSeoMessage(i, lang),
    code: i.code,
  }));

  const a11yIssues = (page.accessibility?.issues ?? []).map(
    (i: AccessibilityIssue) => {
      const message = localizeA11yMessage(i, lang);
      return {
        severity: i.severity,
        source: "A11Y",
        message: i.count > 1 ? `${message} (×${i.count})` : message,
        code: i.code,
      };
    }
  );

  const securityIssues = (security?.all_findings ?? []).map((f: SecurityFinding) => ({
    severity: f.severity,
    source: f.category.toUpperCase(),
    message: localizeFinding(f, lang).title,
    code: f.affected_resource ?? "",
  }));

  const hasAnyCategory = page.seo !== null || page.accessibility !== null || security != null;

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card/50">
      {/* Collapsed row */}
      <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div
            className="truncate font-mono text-xs text-muted-foreground"
            title={page.url}
          >
            {shortUrl}
          </div>
          {totalIssues > 0 && (
            <div className="mt-1 font-mono text-[10px]">
              <span className="text-warning">
                {dict.pageResult.issues(totalIssues)}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-6">
          {page.health && (
            <>
              <MetricChip label="HTTP" value={httpLabel} colorClass={httpColor} />
              <MetricChip label="TTFB ms" value={ttfbLabel} colorClass={ttfbColor} />
            </>
          )}
          {page.seo && (
            <MetricChip
              label="SEO"
              value={String(page.seo.score)}
              colorClass={statusColor(scoreStatus(page.seo.score))}
            />
          )}
          {page.accessibility && (
            <MetricChip
              label="A11Y"
              value={String(page.accessibility.score)}
              colorClass={statusColor(scoreStatus(page.accessibility.score))}
            />
          )}
          {security && (
            <MetricChip
              label="SEC"
              value={String(security.overall_score)}
              colorClass={statusColor(scoreStatus(security.overall_score))}
            />
          )}
          {hasAnyCategory && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="shrink-0 rounded border border-border px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-muted-foreground transition-colors hover:border-accent hover:text-accent"
            >
              {expanded ? dict.pageResult.hide : dict.pageResult.details}
            </button>
          )}
        </div>
      </div>

      {/* Expanded section */}
      {expanded && (
        <div className="border-t border-border px-4 py-5 space-y-6">
          {/* Score ring + metrics row */}
          <div className="flex flex-wrap items-center gap-8">
            {pageScore !== null && (
              <div className="flex flex-col items-center gap-2">
                <ScoreRing score={pageScore} status={pageStatus} />
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {dict.pageResult.pageScore}
                </span>
              </div>
            )}

            <div className="flex flex-wrap gap-6">
              {page.health && (
                <div className="space-y-3">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {dict.pageResult.health}
                  </span>
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-muted-foreground w-16">
                        {dict.pageResult.status}
                      </span>
                      <span className={`font-mono text-sm font-bold ${httpColor}`}>
                        {httpLabel}{" "}
                        {page.health.is_available ? "✓" : "✗"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-muted-foreground w-16">
                        {dict.pageResult.ttfb}
                      </span>
                      <span className={`font-mono text-sm font-bold ${ttfbColor}`}>
                        {ttfbLabel}
                      </span>
                    </div>
                    {page.health.has_redirect_loop && (
                      <div className="font-mono text-[10px] text-destructive">
                        {dict.pageResult.redirectLoop}
                      </div>
                    )}
                    {page.health.redirect_chain.length > 0 && (
                      <div className="font-mono text-[10px] text-muted-foreground">
                        {dict.pageResult.redirects(page.health.redirect_chain.length)}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {page.seo && (
                <div className="space-y-1">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {dict.pageResult.seoScore}
                  </span>
                  <div
                    className={`font-mono text-3xl font-bold ${statusColor(scoreStatus(page.seo.score))}`}
                  >
                    {page.seo.score}
                  </div>
                </div>
              )}

              {page.accessibility && (
                <div className="space-y-1">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {dict.pageResult.a11yScore}
                  </span>
                  <div
                    className={`font-mono text-3xl font-bold ${statusColor(scoreStatus(page.accessibility.score))}`}
                  >
                    {page.accessibility.score}
                  </div>
                </div>
              )}

              {security && (
                <div className="space-y-1">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {dict.pageResult.securityScore}
                  </span>
                  <div
                    className={`font-mono text-3xl font-bold ${statusColor(scoreStatus(security.overall_score))}`}
                  >
                    {security.overall_score}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Per-category issues */}
          {page.seo && (
            <IssueSection title={dict.pageResult.seoIssues} issues={seoIssues} />
          )}
          {page.accessibility && (
            <IssueSection title={dict.pageResult.accessibilityIssues} issues={a11yIssues} />
          )}
          {security && (
            <IssueSection title={dict.pageResult.securityFindings} issues={securityIssues} />
          )}
        </div>
      )}
    </div>
  );
}
