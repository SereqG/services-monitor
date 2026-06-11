// Polish templates for backend-generated findings, keyed by their stable `code`.
// English stays the deterministic source of truth (rendered straight from the
// backend); Polish is rendered here by interpolating the finding's `params`.
// Any code without a Polish template falls back to the backend English text.

import type { AccessibilityIssue, SecurityFinding, SeoIssue } from "@/lib/types/api";
import { interpolate } from "./interpolate";
import type { Language } from "./types";

type FindingTemplate = {
  title: string;
  description?: string;
  remediation?: string;
};

const SECURITY_FINDINGS_PL: Record<string, FindingTemplate> = {
  MISSING_SECURITY_HEADER: {
    title: "Brak nagłówka {header}",
    description:
      "Brakuje nagłówka bezpieczeństwa {header}, co osłabia ochronę przeglądarki.",
    remediation: "Dodaj nagłówek {header} do odpowiedzi serwera.",
  },
  HTTPS_NOT_USED: {
    title: "Nie używasz HTTPS",
    description: "Adres nie korzysta z HTTPS, przez co ruch może zostać przechwycony.",
    remediation:
      "Przekieruj cały ruch HTTP na HTTPS i skonfiguruj ważny certyfikat TLS.",
  },
  WEAK_TLS_VERSION: {
    title: "Słaba wersja TLS: {version}",
    description: "{version} jest przestarzała i kryptograficznie słaba.",
    remediation: "Wyłącz TLS 1.0 i TLS 1.1. Wymagaj TLS 1.2 lub TLS 1.3.",
  },
  TLS_CERT_EXPIRED: {
    title: "Przeterminowany certyfikat TLS",
    description: "Certyfikat TLS wygasł i będzie powodować błędy w przeglądarce.",
    remediation: "Natychmiast odnów certyfikat TLS.",
  },
  TLS_CERT_EXPIRING_SOON: {
    title: "Certyfikat TLS wygasa w ciągu 14 dni",
    description: "Certyfikat wygasa za {days} dni.",
    remediation: "Odnów certyfikat TLS przed wygaśnięciem.",
  },
  TLS_CERT_EXPIRING: {
    title: "Certyfikat TLS wygasa w ciągu 30 dni",
    description: "Certyfikat wygasa za {days} dni.",
    remediation: "Zaplanuj odnowienie certyfikatu TLS.",
  },
  TLS_CERT_VERIFICATION_FAILED: {
    title: "Weryfikacja certyfikatu TLS nie powiodła się",
    description: "Błąd weryfikacji SSL: {error}",
    remediation: "Napraw certyfikat TLS (sprawdź łańcuch, nazwę hosta, datę ważności).",
  },
  TLS_HANDSHAKE_FAILED: {
    title: "Uzgadnianie TLS nie powiodło się",
    description: "Błąd SSL podczas połączenia: {error}",
    remediation: "Sprawdź i popraw konfigurację TLS.",
  },
  TLS_UNREACHABLE: {
    title: "Nie można nawiązać połączenia TLS",
    description: "Nie udało się połączyć, aby sprawdzić TLS: {error}",
    remediation: "Sprawdź, czy host jest dostępny i TLS jest skonfigurowany.",
  },
  COOKIE_MISSING_SECURE: {
    title: "Brak flagi Secure w ciasteczku „{cookie}”",
    description: "Ciasteczko może być przesyłane przez nieszyfrowane połączenia HTTP.",
    remediation:
      "Dodaj flagę Secure do ciasteczek, które powinny być wysyłane tylko przez HTTPS.",
  },
  COOKIE_MISSING_HTTPONLY: {
    title: "Brak flagi HttpOnly w ciasteczku „{cookie}”",
    description:
      "Ciasteczko jest dostępne z poziomu JavaScript, co zwiększa ryzyko XSS.",
    remediation:
      "Dodaj flagę HttpOnly do ciasteczek, które nie wymagają dostępu z JavaScript.",
  },
  COOKIE_MISSING_SAMESITE: {
    title: "Brak atrybutu SameSite w ciasteczku „{cookie}”",
    description:
      "Ciasteczko jest wysyłane przy wszystkich żądaniach z innych domen, co zwiększa ryzyko CSRF.",
    remediation: "Ustaw SameSite=Strict lub SameSite=Lax dla ciasteczek sesji.",
  },
  COOKIE_SAMESITE_NONE_INSECURE: {
    title: "SameSite=None bez Secure w ciasteczku „{cookie}”",
    description: "SameSite=None jest nieprawidłowe bez flagi Secure.",
    remediation: "Dodaj flagę Secure przy użyciu SameSite=None.",
  },
  MISSING_SPF: {
    title: "Brak rekordu SPF",
    description:
      "Nie znaleziono rekordu SPF. Sender Policy Framework nie jest egzekwowany.",
    remediation: "Dodaj rekord TXT z polityką SPF (np. 'v=spf1 include:... -all').",
  },
  MISSING_DMARC: {
    title: "Brak rekordu DMARC",
    description:
      "Nie znaleziono polityki DMARC. Podszywanie się w e-mailach nie jest ograniczane.",
    remediation: "Dodaj rekord TXT DMARC (np. 'v=DMARC1; p=quarantine').",
  },
  MISSING_CAA: {
    title: "Brak rekordu CAA",
    description:
      "Żaden rekord CAA nie ogranicza wystawiania certyfikatów dla tej domeny.",
    remediation:
      "Dodaj rekordy CAA, aby określić, które urzędy mogą wystawiać certyfikaty.",
  },
  DNSSEC_NOT_ENABLED: {
    title: "DNSSEC nie jest włączony",
    description:
      "DNSSEC nie jest skonfigurowany. Odpowiedzi DNS nie mogą być kryptograficznie weryfikowane.",
    remediation:
      "Włącz DNSSEC u rejestratora domeny, aby chronić się przed fałszowaniem DNS.",
  },
  MIXED_CONTENT: {
    title: "Wykryto mieszaną treść",
    description: "Znaleziono {count} zasob(ów) HTTP na stronie HTTPS.",
    remediation:
      "Serwuj wszystkie zasoby przez HTTPS, aby uniknąć ostrzeżeń o mieszanej treści.",
  },
  TECHNOLOGY_DETECTED: {
    title: "Wykryto technologię: {technology}",
    description: "Na stronie zidentyfikowano {technology}.",
  },
  MISSING_SECURITY_TXT: {
    title: "Brak pliku security.txt",
    description:
      "Nie znaleziono pliku security.txt pod /.well-known/security.txt ani /security.txt.",
    remediation:
      "Utwórz plik security.txt zgodnie z RFC 9116, aby określić politykę zgłaszania podatności.",
  },
  SOURCE_MAPS_EXPOSED: {
    title: "Mapy źródeł w zasobach produkcyjnych",
    description:
      "Znaleziono {count} odwoła(ń) sourceMappingURL, które ujawniają kod źródłowy aplikacji.",
    remediation:
      "Wyłącz generowanie map źródeł lub ogranicz dostęp do plików .map w produkcji.",
  },
  OUTDATED_JS_LIBRARY: {
    title: "Nieaktualna biblioteka {library} ({version})",
    description:
      "{library} {version} jest poniżej minimalnej zalecanej wersji {minimum} i może zawierać znane podatności.",
    remediation: "Zaktualizuj {library} do wersji {minimum} lub nowszej.",
  },
  JS_LIBRARY_DETECTED: {
    title: "Wykryto bibliotekę JS: {library} {version}",
    description: "Wykryto {library} w wersji {version} w zasobach strony.",
  },
};

const SEO_ISSUES_PL: Record<string, string> = {
  MISSING_TITLE: "Brak tytułu strony",
  TITLE_TOO_SHORT: "Tytuł zbyt krótki ({length} znaków, min. {min})",
  TITLE_TOO_LONG: "Tytuł zbyt długi ({length} znaków, maks. {max})",
  MISSING_DESCRIPTION: "Brak meta opisu",
  DESC_TOO_SHORT: "Meta opis zbyt krótki ({length} znaków, min. {min})",
  DESC_TOO_LONG: "Meta opis zbyt długi ({length} znaków, maks. {max})",
  MISSING_H1: "Nie znaleziono nagłówka H1",
  MULTIPLE_H1: "Znaleziono wiele nagłówków H1 ({count})",
  MISSING_CANONICAL: "Brak tagu canonical",
  IMAGES_MISSING_ALT: "{count} obraz(ów) bez atrybutu alt",
};

const A11Y_ISSUES_PL: Record<string, string> = {
  IMG_MISSING_ALT: "Obrazy bez atrybutu alt",
  INPUT_MISSING_LABEL: "Pola formularza bez etykiet lub aria-label",
  MISSING_MAIN_LANDMARK: "Nie znaleziono punktu orientacyjnego <main>",
  MISSING_LANG_ATTR: "Element <html> nie ma atrybutu lang",
};

export type LocalizedFinding = {
  title: string;
  description: string;
  remediation: string | null;
};

/** A security finding's title/description/remediation in the active language. */
export function localizeFinding(
  finding: SecurityFinding,
  lang: Language,
): LocalizedFinding {
  const fallback: LocalizedFinding = {
    title: finding.title,
    description: finding.description,
    remediation: finding.remediation ?? null,
  };
  if (lang === "en") return fallback;

  const tpl = SECURITY_FINDINGS_PL[finding.code];
  if (!tpl) return fallback;

  const params = finding.params ?? {};
  return {
    title: interpolate(tpl.title, params),
    description: tpl.description ? interpolate(tpl.description, params) : fallback.description,
    remediation: tpl.remediation ? interpolate(tpl.remediation, params) : fallback.remediation,
  };
}

/** An SEO issue's message in the active language. */
export function localizeSeoMessage(issue: SeoIssue, lang: Language): string {
  if (lang === "en") return issue.message;
  const tpl = SEO_ISSUES_PL[issue.code];
  return tpl ? interpolate(tpl, issue.params ?? {}) : issue.message;
}

/** An accessibility issue's message in the active language. */
export function localizeA11yMessage(issue: AccessibilityIssue, lang: Language): string {
  if (lang === "en") return issue.message;
  return A11Y_ISSUES_PL[issue.code] ?? issue.message;
}
