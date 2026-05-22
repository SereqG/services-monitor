import type { AuditCheckType, DiscoveryResult } from "@/lib/types/api";
import { ScopeSelector } from "@/components/discovery/ScopeSelector";

export function UrlSelectionView({
  discovery,
  selectedUrls,
  selectedChecks,
  onToggle,
  onToggleAll,
  onToggleCheck,
  onAudit,
  onReset,
}: {
  discovery: DiscoveryResult;
  selectedUrls: Set<string>;
  selectedChecks: Set<AuditCheckType>;
  onToggle: (url: string) => void;
  onToggleAll: () => void;
  onToggleCheck: (check: AuditCheckType) => void;
  onAudit: () => void;
  onReset: () => void;
}) {
  const allowed = discovery.discovered_urls.filter((u) => u.status === "allowed");
  const blocked = discovery.discovered_urls.filter((u) => u.status === "blocked_by_robots");
  const failed = discovery.discovered_urls.filter((u) => u.status === "fetch_error");
  const rootFailed = failed.some((u) => u.url === discovery.root_url);
  const allSelected = selectedUrls.size === allowed.length && allowed.length > 0;
  const canRunAudit = selectedUrls.size > 0 && selectedChecks.size > 0;

  return (
    <section className="mt-16 space-y-6">
      <div className="flex flex-col gap-1">
        <div className="font-mono text-xs uppercase tracking-widest text-accent">
          Discovery complete — {discovery.duration_seconds.toFixed(1)}s
        </div>
        <h2 className="text-2xl font-bold">
          Found {discovery.total_discovered} pages on{" "}
          {new URL(discovery.root_url).hostname}
        </h2>
        <p className="text-sm text-muted-foreground">
          {discovery.total_allowed} available for audit
          {blocked.length > 0 && `, ${blocked.length} blocked by robots.txt`}
          {failed.length > 0 && `, ${failed.length} failed to fetch`}
          {discovery.hit_limit && (
            <span className="ml-2 text-warning">
              · crawl limit reached — results may be incomplete
            </span>
          )}
        </p>
        {rootFailed && (
          <p className="mt-1 text-sm text-destructive">
            The root URL could not be fetched. Check that the site is reachable and try again.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-xl border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-5 py-3">
            <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              Select pages to audit
            </span>
            <button
              onClick={onToggleAll}
              className="font-mono text-[11px] uppercase tracking-widest text-accent transition-colors hover:text-foreground"
            >
              {allSelected ? "Deselect all" : "Select all"}
            </button>
          </div>

          <ul className="max-h-80 divide-y divide-border overflow-y-auto">
            {allowed.map((u) => (
              <li key={u.url} className="flex items-center gap-3 px-5 py-3 hover:bg-card/80">
                <input
                  type="checkbox"
                  id={u.url}
                  checked={selectedUrls.has(u.url)}
                  onChange={() => onToggle(u.url)}
                  className="size-4 accent-accent"
                />
                <label
                  htmlFor={u.url}
                  className="flex-1 cursor-pointer truncate font-mono text-xs text-foreground"
                >
                  {u.url}
                </label>
                <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                  depth {u.depth}
                </span>
              </li>
            ))}
            {blocked.map((u) => (
              <li key={u.url} className="flex items-center gap-3 px-5 py-3 opacity-40">
                <div className="size-4" />
                <span className="flex-1 truncate font-mono text-xs text-muted-foreground">
                  {u.url}
                </span>
                <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                  robots.txt
                </span>
              </li>
            ))}
            {failed.map((u) => (
              <li key={u.url} className="flex items-center gap-3 px-5 py-3 opacity-50">
                <div className="size-4" />
                <span className="flex-1 truncate font-mono text-xs text-destructive">
                  {u.url}
                </span>
                <span className="shrink-0 font-mono text-[10px] text-destructive">
                  fetch error
                </span>
              </li>
            ))}
          </ul>
        </div>

        <ScopeSelector selectedChecks={selectedChecks} onToggle={onToggleCheck} />
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={onAudit}
          disabled={!canRunAudit}
          className="rounded-md bg-primary px-8 py-3 text-sm font-bold uppercase tracking-tight text-primary-foreground transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          Run audit ({selectedUrls.size} pages · {selectedChecks.size} checks)
        </button>
        <button
          onClick={onReset}
          className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground transition-colors hover:text-foreground"
        >
          ← Start over
        </button>
      </div>
    </section>
  );
}
