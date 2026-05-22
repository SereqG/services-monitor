import type { AuditReport, CategoryResult } from "@/lib/types/api";
import { scoreStatus, statusColor, statusBar, ttfbStatus, type MetricStatus } from "@/lib/utils/scoring";
import { ScoreRing } from "@/components/ui/ScoreRing";
import { StatRow } from "@/components/ui/StatRow";
import { CategoryCard } from "@/components/audit/CategoryCard";
import { HealthDetails } from "@/components/audit/HealthDetails";
import { SeoDetails } from "@/components/audit/SeoDetails";
import { AccessibilityDetails } from "@/components/audit/AccessibilityDetails";
import { SecurityDetails } from "@/components/audit/SecurityDetails";
import { PageResultCard } from "@/components/audit/PageResultCard";
import { AiSummaryCard } from "@/components/audit/AiSummaryCard";

function TestSection({
  category,
  children,
}: {
  category: CategoryResult | undefined;
  children: React.ReactNode;
}) {
  if (!category || category.status === "not_included") return null;
  if (category.status === "error") {
    return (
      <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5">
        <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {category.name}
        </div>
        <p className="text-sm text-destructive">{category.error}</p>
      </div>
    );
  }
  return <>{children}</>;
}

export function ReportView({ report }: { report: AuditReport }) {
  const { score_breakdown, health, seo, accessibility, discovery } = report;
  const overall = score_breakdown.overall_score;
  const overallStatus = overall !== null ? scoreStatus(overall) : "bad";
  const generatedAt = new Date(report.generated_at).toLocaleString();

  const categoryByName = Object.fromEntries(score_breakdown.categories.map((c) => [c.name, c]));

  const coreMetrics: { label: string; value: string; description: string; fill: number; status: MetricStatus }[] = [];

  if (health !== null) {
    const ttfb = health.ttfb_ms;
    coreMetrics.push({
      label: "TTFB",
      value: ttfb !== null ? `${ttfb.toFixed(0)}ms` : "N/A",
      description: "Time to First Byte — how fast the server responds.",
      fill: ttfb !== null ? Math.max(0, Math.round((1 - ttfb / 3000) * 100)) : 50,
      status: ttfbStatus(ttfb),
    });
  }

  if (seo !== null) {
    coreMetrics.push({
      label: "SEO",
      value: `${seo.score}`,
      description: "SEO score based on meta tags, headings, canonical, and structured data.",
      fill: seo.score,
      status: scoreStatus(seo.score),
    });
  }

  if (accessibility !== null) {
    coreMetrics.push({
      label: "A11Y",
      value: `${accessibility.score}`,
      description: "Accessibility score from HTML heuristics (Phase 2 adds axe-core).",
      fill: accessibility.score,
      status: scoreStatus(accessibility.score),
    });
  }

  const blockedCount = discovery.total_discovered - discovery.total_allowed;

  return (
    <section className="mt-20 space-y-12">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-3 border-b border-border pb-6 md:flex-row md:items-end">
        <div>
          <div className="mb-1 font-mono text-xs text-accent">
            AUDIT_COMPLETE // {generatedAt}
          </div>
          <h2 className="flex items-center gap-3 text-2xl font-bold">
            {report.report_name}
            {score_breakdown.grade && (
              <span
                className={`rounded px-2 py-0.5 font-mono text-lg font-bold ${statusColor(overallStatus)}`}
              >
                {score_breakdown.grade}
              </span>
            )}
          </h2>
        </div>
        {health !== null && (
          <div className="md:text-right">
            <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Health
            </div>
            <div
              className={`text-sm font-medium ${health.is_available ? "text-accent" : "text-destructive"}`}
            >
              {health.is_available ? "Available" : "Unavailable"} · HTTP{" "}
              {health.status_code ?? "—"}
            </div>
          </div>
        )}
      </div>

      {/* AI summary (only present when requested) */}
      <AiSummaryCard summary={report.ai_summary} />

      {/* Score ring + core metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card p-8 text-center">
          {overall !== null ? (
            <ScoreRing score={overall} status={overallStatus} />
          ) : (
            <div className="font-mono text-4xl font-bold text-muted-foreground">N/A</div>
          )}
          <span className="mt-4 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
            Overall score
          </span>
        </div>

        {coreMetrics.length > 0 && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3 md:col-span-3">
            {coreMetrics.map((m) => (
              <div key={m.label} className="rounded-xl border border-border bg-card p-6">
                <div className="mb-4 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {m.label}
                </div>
                <div className={`mb-1 font-mono text-3xl font-bold ${statusColor(m.status)}`}>
                  {m.value}
                </div>
                <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
                  <div className={`h-full ${statusBar(m.status)}`} style={{ width: `${m.fill}%` }} />
                </div>
                <p className="mt-4 text-xs leading-normal text-muted-foreground">{m.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Score breakdown */}
      <div className="space-y-4">
        <h3 className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
          Score breakdown
        </h3>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {score_breakdown.categories.map((c) => (
            <CategoryCard key={c.name} category={c} />
          ))}
        </div>
      </div>

      {/* Detailed test results */}
      <div className="space-y-8">
        <h3 className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
          Test results
        </h3>
        <TestSection category={categoryByName["health"]}>
          {health && <HealthDetails health={health} />}
        </TestSection>
        <TestSection category={categoryByName["seo"]}>
          {seo && <SeoDetails seo={seo} />}
        </TestSection>
        <TestSection category={categoryByName["accessibility"]}>
          {accessibility && <AccessibilityDetails accessibility={accessibility} />}
        </TestSection>
        <TestSection category={categoryByName["security"]}>
          {report.security && <SecurityDetails security={report.security} />}
        </TestSection>
      </div>

      {/* Discovery summary */}
      <div className="space-y-4">
        <h3 className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
          Discovery summary
        </h3>
        <div className="overflow-hidden rounded-xl border border-border bg-card/50">
          <ul className="divide-y divide-border">
            <StatRow label="Pages discovered" value={String(discovery.total_discovered)} />
            <StatRow label="Pages available" value={String(discovery.total_allowed)} />
            <StatRow label="Blocked by robots.txt" value={String(blockedCount)} />
            <StatRow label="Crawl duration" value={`${discovery.duration_seconds.toFixed(2)}s`} />
            <StatRow
              label="Sitemap found"
              value={discovery.robots_policy.sitemap_urls.length > 0 ? "Yes" : "No"}
            />
            <StatRow
              label="Robots.txt fetched"
              value={discovery.robots_policy.fetched ? "Yes" : "No"}
            />
          </ul>
        </div>
        {discovery.hit_limit && (
          <div className="rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-xs text-warning">
            Crawl limit reached — some pages may not have been discovered.
          </div>
        )}
      </div>

      {/* Per-subpage results */}
      {report.page_results.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
            Pages audited ({report.page_results.length})
          </h3>
          <div className="space-y-3">
            {report.page_results.map((page) => (
              <PageResultCard key={page.url} page={page} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
