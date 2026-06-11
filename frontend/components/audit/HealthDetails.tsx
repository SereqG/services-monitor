"use client";

import type { HealthCheckResult } from "@/lib/types/api";
import { useI18n } from "@/lib/i18n";

function Row({ label, value, note, pass }: { label: string; value: string; note?: string; pass?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border py-3 last:border-0">
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium">{label}</span>
        {note && <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">{note}</p>}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="font-mono text-sm">{value}</span>
        {pass !== undefined && (
          <span className={`font-mono text-[10px] ${pass ? "text-accent" : "text-destructive"}`}>
            {pass ? "✓" : "✗"}
          </span>
        )}
      </div>
    </div>
  );
}

export function HealthDetails({ health }: { health: HealthCheckResult }) {
  const { dict } = useI18n();
  const h = dict.healthDetails;
  const ttfbMs = health.ttfb_ms;
  const ttfbLabel =
    ttfbMs === null
      ? dict.common.na
      : ttfbMs < 200
      ? `${ttfbMs.toFixed(0)}ms (${h.ttfbQuality.excellent})`
      : ttfbMs < 800
      ? `${ttfbMs.toFixed(0)}ms (${h.ttfbQuality.good})`
      : `${ttfbMs.toFixed(0)}ms (${h.ttfbQuality.slow})`;

  const statusText = h.statusLabels[health.status] ?? health.status;

  return (
    <div>
      <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
        {h.title}
      </h3>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <Row
          label={h.rows.availability.label}
          note={h.rows.availability.note}
          value={health.is_available ? dict.common.available : dict.common.unavailable}
          pass={health.is_available}
        />
        <Row
          label={h.rows.status.label}
          note={h.rows.status.note}
          value={health.status_code !== null ? `${health.status_code} ${statusText}` : statusText}
          pass={health.is_available}
        />
        <Row
          label={h.rows.ttfb.label}
          note={h.rows.ttfb.note}
          value={ttfbLabel}
          pass={ttfbMs !== null && ttfbMs < 800}
        />
        <Row
          label={h.rows.finalUrl.label}
          note={h.rows.finalUrl.note}
          value={health.final_url}
        />
        <Row
          label={h.rows.redirects.label}
          note={h.rows.redirects.note}
          value={String(health.redirect_chain.length)}
          pass={!health.has_redirect_loop}
        />
        {health.has_redirect_loop && (
          <div className="py-3 font-mono text-xs text-destructive">
            {h.redirectLoopDetected}
          </div>
        )}
        {health.error && (
          <div className="py-3 font-mono text-xs text-destructive">{h.errorPrefix}: {health.error}</div>
        )}
      </div>
      {health.redirect_chain.length > 0 && (
        <div className="mt-3 overflow-hidden rounded-xl border border-border bg-card/30 px-4 py-3">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {h.redirectChain}
          </div>
          {health.redirect_chain.map((hop, i) => (
            <div key={i} className="truncate font-mono text-xs text-muted-foreground">
              {hop.status_code} → {hop.url}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
