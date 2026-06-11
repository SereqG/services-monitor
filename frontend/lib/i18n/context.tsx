"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { en, type Dictionary } from "./en";
import { pl } from "./pl";
import { LANGUAGE_COOKIE, type Language } from "./types";

const DICTIONARIES: Record<Language, Dictionary> = { en, pl };

interface I18nValue {
  lang: Language;
  setLanguage: (lang: Language) => void;
  dict: Dictionary;
}

const I18nContext = createContext<I18nValue | null>(null);

// One year; a UI preference, not security-sensitive, so a plain client cookie is fine.
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

function persistLanguage(lang: Language): void {
  document.cookie = `${LANGUAGE_COOKIE}=${lang}; path=/; max-age=${COOKIE_MAX_AGE}; samesite=lax`;
  document.documentElement.lang = lang;
}

export function LanguageProvider({
  initialLanguage,
  children,
}: {
  initialLanguage: Language;
  children: React.ReactNode;
}) {
  const [lang, setLang] = useState<Language>(initialLanguage);

  const setLanguage = useCallback((next: Language) => {
    setLang(next);
    persistLanguage(next);
  }, []);

  const value = useMemo<I18nValue>(
    () => ({ lang, setLanguage, dict: DICTIONARIES[lang] }),
    [lang, setLanguage],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within a LanguageProvider");
  }
  return ctx;
}
