"use client";

import { useI18n } from "@/lib/i18n";
import { LANGUAGES, type Language } from "@/lib/i18n";

function LanguageToggle() {
  const { lang, setLanguage, dict } = useI18n();
  return (
    <div
      className="flex items-center gap-1 rounded-md border border-border p-0.5"
      role="group"
      aria-label={dict.language.label}
    >
      {LANGUAGES.map((code: Language) => {
        const active = code === lang;
        return (
          <button
            key={code}
            type="button"
            onClick={() => setLanguage(code)}
            aria-pressed={active}
            className={`rounded px-2 py-1 font-mono text-[11px] font-bold uppercase tracking-widest transition-colors ${
              active
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {dict.language[code]}
          </button>
        );
      })}
    </div>
  );
}

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-border px-6 md:px-8">
      <div className="flex items-center gap-2">
        <div className="size-6 rounded-sm bg-accent" />
        <span className="font-mono text-lg font-bold uppercase tracking-tighter">
          Velocity.Lab
        </span>
      </div>
      <LanguageToggle />
    </header>
  );
}
