import type { AuditCheckType } from "@/lib/types/api";

const CHECKS: { type: AuditCheckType; label: string; description: string }[] = [
  { type: "health", label: "Health", description: "HTTP status, redirects, availability, TTFB" },
  { type: "seo", label: "SEO", description: "Meta tags, headings, canonical, structured data" },
  { type: "accessibility", label: "Accessibility", description: "ARIA, alt text, heading structure" },
  { type: "security", label: "Security", description: "HTTP security response headers" },
];

export function ScopeSelector({
  selectedChecks,
  onToggle,
}: {
  selectedChecks: Set<AuditCheckType>;
  onToggle: (check: AuditCheckType) => void;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="border-b border-border px-5 py-3">
        <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
          Checks to run
        </span>
      </div>
      <ul className="divide-y divide-border">
        {CHECKS.map((check) => (
          <li key={check.type} className="flex items-center gap-3 px-5 py-3 hover:bg-card/80">
            <input
              type="checkbox"
              id={`check-${check.type}`}
              checked={selectedChecks.has(check.type)}
              onChange={() => onToggle(check.type)}
              className="size-4 accent-accent"
            />
            <label htmlFor={`check-${check.type}`} className="flex-1 cursor-pointer">
              <span className="font-mono text-xs text-foreground">{check.label}</span>
              <span className="ml-2 font-mono text-[10px] text-muted-foreground">
                {check.description}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
