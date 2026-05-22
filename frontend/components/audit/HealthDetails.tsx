import type { HealthCheckResult } from "@/lib/types/api";
import { ttfbStatus, statusColor } from "@/lib/utils/scoring";

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
  const ttfbMs = health.ttfb_ms;
  const ttfbLabel =
    ttfbMs === null
      ? "N/A"
      : ttfbMs < 200
      ? `${ttfbMs.toFixed(0)}ms (excellent)`
      : ttfbMs < 800
      ? `${ttfbMs.toFixed(0)}ms (good)`
      : `${ttfbMs.toFixed(0)}ms (slow)`;

  const statusLabel: Record<string, string> = {
    ok: "OK",
    redirect: "Redirect",
    client_error: "Client error",
    server_error: "Server error",
    timeout: "Timeout",
    connection_error: "Connection error",
  };

  return (
    <div>
      <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
        Health check
      </h3>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <Row
          label="Availability"
          note="Site responds with HTTP 2xx or 3xx"
          value={health.is_available ? "Available" : "Unavailable"}
          pass={health.is_available}
        />
        <Row
          label="HTTP status"
          note="Final response code after following redirects"
          value={health.status_code !== null ? `${health.status_code} ${statusLabel[health.status] ?? health.status}` : statusLabel[health.status] ?? health.status}
          pass={health.is_available}
        />
        <Row
          label="Time to First Byte"
          note="How fast the server sent the first response byte. < 200ms excellent, < 800ms good, > 800ms slow."
          value={ttfbLabel}
          pass={ttfbMs !== null && ttfbMs < 800}
        />
        <Row
          label="Final URL"
          note="Destination URL after all redirects"
          value={health.final_url}
        />
        <Row
          label="Redirects"
          note="Number of HTTP 3xx hops before reaching the final URL. Chains longer than 3 hops add latency."
          value={String(health.redirect_chain.length)}
          pass={!health.has_redirect_loop}
        />
        {health.has_redirect_loop && (
          <div className="py-3 font-mono text-xs text-destructive">
            Redirect loop detected — the chain visits the same URL more than once.
          </div>
        )}
        {health.error && (
          <div className="py-3 font-mono text-xs text-destructive">Error: {health.error}</div>
        )}
      </div>
      {health.redirect_chain.length > 0 && (
        <div className="mt-3 overflow-hidden rounded-xl border border-border bg-card/30 px-4 py-3">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Redirect chain
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
