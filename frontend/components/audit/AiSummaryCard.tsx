"use client";

import type { AiSummary } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n";

function IssueList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2">
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        {title}
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li
            key={i}
            className="flex gap-2 text-sm leading-normal text-foreground/90"
          >
            <span className="text-accent">›</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AiSummaryCard({ summary }: { summary: AiSummary | null }) {
  const { dict } = useI18n();
  // AI was not requested for this audit — render nothing.
  if (!summary) return null;

  const heading = (
    <div className="flex items-center gap-3">
      <h3 className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
        {dict.aiSummary.heading}
      </h3>
      {summary.model && (
        <span className="font-mono text-[10px] text-muted-foreground/60">
          {summary.model}
        </span>
      )}
    </div>
  );

  if (summary.status === "error" || !summary.summary) {
    return (
      <div className="space-y-4">
        {heading}
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-5">
          <p className="text-sm text-destructive">
            {summary.error ?? dict.aiSummary.generationFailed}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {dict.aiSummary.unaffectedNote}
          </p>
        </div>
      </div>
    );
  }

  const overview = summary.summary;
  const hasStrengthsOrWeaknesses =
    overview.main_strengths.length > 0 || overview.main_weaknesses.length > 0;

  return (
    <div className="space-y-4">
      {heading}

      <div className="space-y-6 rounded-xl border border-accent/30 bg-card p-6">
        <p className="text-sm leading-relaxed text-foreground/90">
          {overview.overall_assessment}
        </p>

        {hasStrengthsOrWeaknesses && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <IssueList title={dict.aiSummary.strengths} items={overview.main_strengths} />
            <IssueList title={dict.aiSummary.weaknesses} items={overview.main_weaknesses} />
          </div>
        )}

        <IssueList
          title={dict.aiSummary.priorityRecommendations}
          items={overview.priority_recommendations}
        />
      </div>

      {summary.problematic_pages.length > 0 && (
        <div className="space-y-3">
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {dict.aiSummary.pagesNeedingAttention}
          </div>
          {summary.problematic_pages.map((page) => (
            <div
              key={page.url}
              className="space-y-3 rounded-xl border border-border bg-card/50 p-5"
            >
              <div className="break-all font-mono text-xs text-accent">
                {page.url}
              </div>
              <p className="text-sm leading-normal text-foreground/90">
                {page.summary}
              </p>
              <IssueList
                title={dict.aiSummary.recommendedActions}
                items={page.recommended_actions}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
