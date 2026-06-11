"use client";

import type { AuditCheckType } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n";

const CHECK_TYPES: AuditCheckType[] = ["health", "seo", "accessibility", "security"];

export function ScopeSelector({
  selectedChecks,
  onToggle,
}: {
  selectedChecks: Set<AuditCheckType>;
  onToggle: (check: AuditCheckType) => void;
}) {
  const { dict } = useI18n();
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="border-b border-border px-5 py-3">
        <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
          {dict.scope.checksToRun}
        </span>
      </div>
      <ul className="divide-y divide-border">
        {CHECK_TYPES.map((type) => {
          const check = dict.scope.checks[type];
          return (
            <li key={type} className="flex items-center gap-3 px-5 py-3 hover:bg-card/80">
              <input
                type="checkbox"
                id={`check-${type}`}
                checked={selectedChecks.has(type)}
                onChange={() => onToggle(type)}
                className="size-4 accent-accent"
              />
              <label htmlFor={`check-${type}`} className="flex-1 cursor-pointer">
                <span className="font-mono text-xs text-foreground">{check.label}</span>
                <span className="ml-2 font-mono text-[10px] text-muted-foreground">
                  {check.description}
                </span>
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
