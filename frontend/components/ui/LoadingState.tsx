export function LoadingState({ message }: { message: string }) {
  return (
    <section className="mt-16 space-y-4">
      <div className="font-mono text-xs uppercase tracking-widest text-accent">{message}</div>
      <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
        <div className="h-full w-1/3 animate-pulse rounded-full bg-accent" />
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        <div className="h-48 animate-pulse rounded-xl border border-border bg-card/50" />
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3 md:col-span-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl border border-border bg-card/50" />
          ))}
        </div>
      </div>
    </section>
  );
}
