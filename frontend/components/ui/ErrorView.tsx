export function ErrorView({ message, onReset }: { message: string; onReset: () => void }) {
  return (
    <section className="mt-16 rounded-xl border border-destructive/40 bg-destructive/10 p-8">
      <div className="mb-2 font-mono text-xs uppercase tracking-widest text-destructive">
        Error
      </div>
      <p className="mb-6 text-sm text-muted-foreground">{message}</p>
      <button
        onClick={onReset}
        className="rounded-md bg-primary px-6 py-2 text-sm font-bold uppercase tracking-tight text-primary-foreground transition-colors hover:bg-white"
      >
        Try again
      </button>
    </section>
  );
}
