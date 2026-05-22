export function IdlePlaceholder() {
  return (
    <section className="mt-20 rounded-2xl border border-dashed border-border bg-card/30 p-10 text-center">
      <div className="mx-auto max-w-md">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          Awaiting input
        </div>
        <p className="mt-3 text-sm text-muted-foreground">
          Enter a URL and email to begin. We&apos;ll first crawl the site to discover pages, then
          you can choose which ones to audit.
        </p>
      </div>
    </section>
  );
}
