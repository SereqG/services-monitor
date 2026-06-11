"use client";

import type { AccessibilityResult, AccessibilityIssue, AccessibilitySeverity } from "@/lib/types/api";
import { issueSeverityColor } from "@/lib/utils/scoring";
import { useI18n } from "@/lib/i18n";

// Each check is identified by the backend issue `code`; labels/notes are localized.
const CHECKS: Array<{ code: string; row: "lang" | "alt" | "label" | "main" }> = [
  { code: "MISSING_LANG_ATTR", row: "lang" },
  { code: "IMG_MISSING_ALT", row: "alt" },
  { code: "INPUT_MISSING_LABEL", row: "label" },
  { code: "MISSING_MAIN_LANDMARK", row: "main" },
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
  const { dict } = useI18n();
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
              {dict.severity[issue.severity] ?? issue.severity}
            </span>
            {issue.count > 1 && (
              <span className="font-mono text-xs text-muted-foreground">×{issue.count}</span>
            )}
          </>
        ) : (
          <span className="font-mono text-[10px] text-accent">✓ {dict.common.pass}</span>
        )}
      </div>
    </div>
  );
}

export function AccessibilityDetails({ accessibility }: { accessibility: AccessibilityResult }) {
  const { dict } = useI18n();
  const t = dict.accessibilityDetails;
  const issuesByCode = Object.fromEntries(accessibility.issues.map((i) => [i.code, i]));

  return (
    <div>
      <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
        {t.title}
      </h3>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        {CHECKS.map((check) => (
          <CheckRow
            key={check.code}
            label={t.rows[check.row].label}
            note={t.rows[check.row].note}
            issue={issuesByCode[check.code]}
          />
        ))}
      </div>
      {accessibility.note && (
        <div className="mt-3 rounded-xl border border-border bg-card/30 p-4">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {t.auditScope}
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">{accessibility.note}</p>
        </div>
      )}
    </div>
  );
}
