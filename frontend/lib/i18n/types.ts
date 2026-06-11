export type Language = "en" | "pl";

export const LANGUAGES: Language[] = ["en", "pl"];

export const LANGUAGE_COOKIE = "lang";

export function isLanguage(value: unknown): value is Language {
  return value === "en" || value === "pl";
}
