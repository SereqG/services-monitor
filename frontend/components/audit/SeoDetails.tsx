import type { SeoAnalysisResult, SeoIssue, Severity } from "@/lib/types/api";
import { issueSeverityColor } from "@/lib/utils/scoring";

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
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-card/50 p-3">
      <span
        className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[9px] uppercase ${issueSeverityColor(issue.severity as Severity)}`}
      >
        {issue.severity}
      </span>
      <div>
        <p className="text-sm font-medium">{issue.message}</p>
        <p className="font-mono text-[10px] text-muted-foreground">{issue.code}</p>
        {issue.detail && <p className="mt-0.5 text-xs text-muted-foreground">{issue.detail}</p>}
      </div>
    </div>
  );
}

const TITLE_MIN = 30;
const TITLE_MAX = 60;
const DESC_MIN = 120;
const DESC_MAX = 160;

export function SeoDetails({ seo }: { seo: SeoAnalysisResult }) {
  const { meta, headings } = seo;

  const titleLen = meta.title_length;
  const titleOk = !!titleLen && titleLen >= TITLE_MIN && titleLen <= TITLE_MAX;
  const titleWarn = !!titleLen && (titleLen < TITLE_MIN || titleLen > TITLE_MAX);

  const descLen = meta.description_length;
  const descOk = !!descLen && descLen >= DESC_MIN && descLen <= DESC_MAX;
  const descWarn = !!descLen && (descLen < DESC_MIN || descLen > DESC_MAX);

  return (
    <div>
      <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
        SEO checks
      </h3>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label="Page title"
          note={`Optimal length: ${TITLE_MIN}–${TITLE_MAX} chars. Affects how the page appears in search results.`}
          value={
            meta.title
              ? `"${meta.title.length > 50 ? meta.title.slice(0, 47) + "…" : meta.title}" (${titleLen} chars)`
              : "Missing"
          }
          pass={titleOk}
          warn={titleWarn}
        />
        <CheckRow
          label="Meta description"
          note={`Optimal length: ${DESC_MIN}–${DESC_MAX} chars. Shown as the snippet in search results.`}
          value={
            meta.description
              ? `${descLen} chars`
              : "Missing"
          }
          pass={descOk}
          warn={descWarn}
        />
        <CheckRow
          label="H1 heading"
          note="Every page should have exactly one H1 — the primary topic of the page."
          value={
            headings.h1_count === 0
              ? "Missing"
              : headings.h1_count === 1
              ? `"${headings.h1_texts[0]?.slice(0, 60) ?? ""}"`
              : `${headings.h1_count} found (too many)`
          }
          pass={headings.h1_count === 1}
          warn={headings.h1_count > 1}
        />
        <CheckRow
          label="H2 / H3 headings"
          note="Subheadings help structure content for readers and search engines."
          value={`${headings.h2_count} H2, ${headings.h3_count} H3`}
          pass={true}
        />
        <CheckRow
          label="Canonical tag"
          note="Tells search engines the preferred URL for this page, preventing duplicate-content issues."
          value={meta.canonical ?? "Missing"}
          pass={!!meta.canonical}
        />
        <CheckRow
          label="Schema markup"
          note="Structured data (JSON-LD) helps search engines understand page content and enables rich results."
          value={seo.has_schema_markup ? "Present" : "Missing"}
          pass={seo.has_schema_markup}
          warn={!seo.has_schema_markup}
        />
        <CheckRow
          label="Images without alt text"
          note="Alt attributes describe images for screen readers and are used by search engines."
          value={seo.images_without_alt === 0 ? "None" : `${seo.images_without_alt} image(s)`}
          pass={seo.images_without_alt === 0}
        />
        <CheckRow
          label="OG title"
          note="Open Graph title controls how the page title appears when shared on social media."
          value={meta.og_title ?? "Missing"}
          pass={!!meta.og_title}
          warn={!meta.og_title}
        />
        <CheckRow
          label="OG description"
          note="Open Graph description shown in social media link previews."
          value={meta.og_description ? `${meta.og_description.length} chars` : "Missing"}
          pass={!!meta.og_description}
          warn={!meta.og_description}
        />
        <CheckRow
          label="OG image"
          note="Open Graph image displayed when the page is shared on social media."
          value={meta.og_image ? "Present" : "Missing"}
          pass={!!meta.og_image}
          warn={!meta.og_image}
        />
        <CheckRow
          label="Robots meta"
          note="Controls whether search engines should index this page and follow its links."
          value={meta.robots_meta ?? "Not set (default: index, follow)"}
          pass={true}
        />
      </div>

      {seo.issues.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Issues ({seo.issues.length})
          </div>
          {seo.issues.map((issue, i) => (
            <IssueRow key={i} issue={issue} />
          ))}
        </div>
      )}
    </div>
  );
}
