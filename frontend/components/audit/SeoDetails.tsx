"use client";

import type { SeoAnalysisResult, SeoIssue, Severity } from "@/lib/types/api";
import { issueSeverityColor } from "@/lib/utils/scoring";
import { useI18n, localizeSeoMessage } from "@/lib/i18n";

function CheckRow({
  label,
  value,
  note,
  pass,
  warn,
}: {
  label: string;
  value: string;
  note: string;
  pass: boolean;
  warn?: boolean;
}) {
  const indicator = pass ? "text-accent" : warn ? "text-warning" : "text-destructive";
  const symbol = pass ? "✓" : warn ? "!" : "✗";
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border py-3 last:border-0">
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium">{label}</span>
        <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">{note}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="max-w-[200px] truncate text-right font-mono text-xs text-muted-foreground">
          {value}
        </span>
        <span className={`font-mono text-[10px] ${indicator}`}>{symbol}</span>
      </div>
    </div>
  );
}

function IssueRow({ issue }: { issue: SeoIssue }) {
  const { lang, dict } = useI18n();
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-card/50 p-3">
      <span
        className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[9px] uppercase ${issueSeverityColor(issue.severity as Severity)}`}
      >
        {dict.severity[issue.severity] ?? issue.severity}
      </span>
      <div>
        <p className="text-sm font-medium">{localizeSeoMessage(issue, lang)}</p>
        <p className="font-mono text-[10px] text-muted-foreground">{issue.code}</p>
        {issue.detail && <p className="mt-0.5 text-xs text-muted-foreground">{issue.detail}</p>}
      </div>
    </div>
  );
}

export function SeoDetails({ seo }: { seo: SeoAnalysisResult }) {
  const { dict } = useI18n();
  const t = dict.seoDetails;
  const { meta, headings } = seo;

  const TITLE_MIN = 30;
  const TITLE_MAX = 60;
  const DESC_MIN = 120;
  const DESC_MAX = 160;

  const titleLen = meta.title_length;
  const titleOk = !!titleLen && titleLen >= TITLE_MIN && titleLen <= TITLE_MAX;
  const titleWarn = !!titleLen && (titleLen < TITLE_MIN || titleLen > TITLE_MAX);

  const descLen = meta.description_length;
  const descOk = !!descLen && descLen >= DESC_MIN && descLen <= DESC_MAX;
  const descWarn = !!descLen && (descLen < DESC_MIN || descLen > DESC_MAX);

  return (
    <div>
      <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
        {t.title}
      </h3>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label={t.rows.title.label}
          note={t.rows.title.note}
          value={
            meta.title
              ? `"${meta.title.length > 50 ? meta.title.slice(0, 47) + "…" : meta.title}" (${t.chars(titleLen ?? 0)})`
              : dict.common.missing
          }
          pass={titleOk}
          warn={titleWarn}
        />
        <CheckRow
          label={t.rows.description.label}
          note={t.rows.description.note}
          value={meta.description ? t.chars(descLen ?? 0) : dict.common.missing}
          pass={descOk}
          warn={descWarn}
        />
        <CheckRow
          label={t.rows.h1.label}
          note={t.rows.h1.note}
          value={
            headings.h1_count === 0
              ? dict.common.missing
              : headings.h1_count === 1
              ? `"${headings.h1_texts[0]?.slice(0, 60) ?? ""}"`
              : t.tooMany(headings.h1_count)
          }
          pass={headings.h1_count === 1}
          warn={headings.h1_count > 1}
        />
        <CheckRow
          label={t.rows.headings.label}
          note={t.rows.headings.note}
          value={t.headingsValue(headings.h2_count, headings.h3_count)}
          pass={true}
        />
        <CheckRow
          label={t.rows.canonical.label}
          note={t.rows.canonical.note}
          value={meta.canonical ?? dict.common.missing}
          pass={!!meta.canonical}
        />
        <CheckRow
          label={t.rows.schema.label}
          note={t.rows.schema.note}
          value={seo.has_schema_markup ? dict.common.present : dict.common.missing}
          pass={seo.has_schema_markup}
          warn={!seo.has_schema_markup}
        />
        <CheckRow
          label={t.rows.images.label}
          note={t.rows.images.note}
          value={seo.images_without_alt === 0 ? dict.common.none : t.imageCount(seo.images_without_alt)}
          pass={seo.images_without_alt === 0}
        />
        <CheckRow
          label={t.rows.ogTitle.label}
          note={t.rows.ogTitle.note}
          value={meta.og_title ?? dict.common.missing}
          pass={!!meta.og_title}
          warn={!meta.og_title}
        />
        <CheckRow
          label={t.rows.ogDescription.label}
          note={t.rows.ogDescription.note}
          value={meta.og_description ? t.chars(meta.og_description.length) : dict.common.missing}
          pass={!!meta.og_description}
          warn={!meta.og_description}
        />
        <CheckRow
          label={t.rows.ogImage.label}
          note={t.rows.ogImage.note}
          value={meta.og_image ? dict.common.present : dict.common.missing}
          pass={!!meta.og_image}
          warn={!meta.og_image}
        />
        <CheckRow
          label={t.rows.robots.label}
          note={t.rows.robots.note}
          value={meta.robots_meta ?? t.robotsDefault}
          pass={true}
        />
      </div>

      {seo.issues.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {t.issuesHeading(seo.issues.length)}
          </div>
          {seo.issues.map((issue, i) => (
            <IssueRow key={i} issue={issue} />
          ))}
        </div>
      )}
    </div>
  );
}
