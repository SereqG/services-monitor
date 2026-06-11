"use client";

import type { CategoryResult } from "@/lib/types/api";
import { scoreStatus, statusColor, statusBar } from "@/lib/utils/scoring";
import { useI18n } from "@/lib/i18n";

export function CategoryCard({ category }: { category: CategoryResult }) {
  const { dict } = useI18n();
  if (category.status === "not_included") return null;

  const name = dict.categories[category.name] ?? category.name;

  if (category.status === "error") {
    return (
      <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-6">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {name}
        </span>
        <p className="mt-3 text-xs leading-normal text-destructive">{category.error}</p>
      </div>
    );
  }

  const status = scoreStatus(category.score!);
  return (
    <div className="rounded-xl border border-border bg-card p-6 transition-colors hover:border-accent/40">
      <div className="mb-4 flex items-start justify-between">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {name}
        </span>
        <span className={`font-mono text-2xl font-bold ${statusColor(status)}`}>
          {category.score}
        </span>
      </div>
      <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
        <div className={`h-full ${statusBar(status)}`} style={{ width: `${category.score}%` }} />
      </div>
    </div>
  );
}
