export function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <li className="flex items-center justify-between px-5 py-3">
      <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
      <span className="font-mono text-xs">{value}</span>
    </li>
  );
}
