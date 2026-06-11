"use client";

import { useI18n } from "@/lib/i18n";

export function IdlePlaceholder() {
  const { dict } = useI18n();
  return (
    <section className="mt-20 rounded-2xl border border-dashed border-border bg-card/30 p-10 text-center">
      <div className="mx-auto max-w-md">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          {dict.idle.awaitingInput}
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{dict.idle.description}</p>
      </div>
    </section>
  );
}
