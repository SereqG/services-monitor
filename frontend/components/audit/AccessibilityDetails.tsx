import type { AccessibilityResult, AccessibilityIssue, AccessibilitySeverity } from "@/lib/types/api";
import { issueSeverityColor } from "@/lib/utils/scoring";

const CHECKS: Array<{
  code: string;
  label: string;
  note: string;
  severity: AccessibilitySeverity;
}> = [
  {
    code: "MISSING_LANG_ATTR",
    label: "HTML language attribute",
    note: "The <html> element must have a lang attribute so screen readers know which language to use.",
    severity: "serious",
  },
  {
    code: "IMG_MISSING_ALT",
    label: "Image alt text",
    note: "All <img> elements must have an alt attribute. Screen readers read it aloud; search engines use it too.",
    severity: "serious",
  },
  {
    code: "INPUT_MISSING_LABEL",
    label: "Form input labels",
    note: "Every visible form input must have an associated label or aria-label so users know what to type.",
    severity: "serious",
  },
  {
    code: "MISSING_MAIN_LANDMARK",
    label: "Main landmark",
    note: "A <main> element (or role='main') lets keyboard and screen reader users skip directly to the main content.",
    severity: "moderate",
  },
];

function CheckRow({
  label,
  note,
  issue,
}: {
  label: string;
  note: string;
  issue: AccessibilityIssue | undefined;
}) {
  const pass = !issue;
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border py-3 last:border-0">
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium">{label}</span>
        <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">{note}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {issue ? (
          <>
            <span
              className={`rounded px-1.5 py-0.5 font-mono text-[9px] uppercase ${issueSeverityColor(issue.severity as AccessibilitySeverity)}`}
            >
              {issue.severity}
            </span>
            {issue.count > 1 && (
              <span className="font-mono text-xs text-muted-foreground">×{issue.count}</span>
            )}
          </>
        ) : (
          <span className="font-mono text-[10px] text-accent">✓ Pass</span>
        )}
      </div>
    </div>
  );
}

export function AccessibilityDetails({ accessibility }: { accessibility: AccessibilityResult }) {
  const issuesByCode = Object.fromEntries(accessibility.issues.map((i) => [i.code, i]));

  return (
    <div>
      <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
        Accessibility checks
      </h3>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        {CHECKS.map((check) => (
          <CheckRow
            key={check.code}
            label={check.label}
            note={check.note}
            issue={issuesByCode[check.code]}
          />
        ))}
      </div>
      {accessibility.note && (
        <div className="mt-3 rounded-xl border border-border bg-card/30 p-4">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Audit scope
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">{accessibility.note}</p>
        </div>
      )}
    </div>
  );
}
