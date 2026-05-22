export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-border px-6 md:px-8">
      <div className="flex items-center gap-2">
        <div className="size-6 rounded-sm bg-accent" />
        <span className="font-mono text-lg font-bold uppercase tracking-tighter">
          Velocity.Lab
        </span>
      </div>
    </header>
  );
}
