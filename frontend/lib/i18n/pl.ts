import type { Dictionary } from "./en";

// Polish UI dictionary. Written as natural, friendly Polish for a non-technical
// website owner — not a literal translation of the English copy.
export const pl: Dictionary = {
  language: {
    label: "Język",
    en: "EN",
    pl: "PL",
    enName: "English",
    plName: "Polski",
  },

  common: {
    missing: "Brak",
    present: "Obecny",
    none: "Brak",
    noneFound: "Nie znaleziono",
    yes: "Tak",
    no: "Nie",
    unknown: "Nieznane",
    valid: "Ważny",
    invalid: "Nieważny",
    enabled: "Włączone",
    disabled: "Wyłączone",
    available: "Dostępna",
    unavailable: "Niedostępna",
    na: "Brak danych",
    pass: "OK",
    unexpectedError: "Wystąpił nieoczekiwany błąd.",
  },

  severity: {
    critical: "krytyczne",
    high: "wysokie",
    medium: "średnie",
    low: "niskie",
    info: "info",
    informational: "informacyjne",
    serious: "poważne",
    moderate: "umiarkowane",
    minor: "drobne",
  },

  categories: {
    health: "Kondycja",
    performance: "Wydajność",
    seo: "SEO",
    accessibility: "Dostępność",
    security: "Bezpieczeństwo",
  },

  home: {
    engineOnline: "Silnik aktywny",
    heroTitle: "Analizuj wydajność strony w czasie rzeczywistym.",
    heroSubtitle:
      "Wklej adres URL, a my przejdziemy po stronie i przeprowadzimy pełny audyt — SEO, dostępność i kondycję techniczną. Wyniki przedstawimy prostym językiem, żebyś od razu wiedział, co poprawić w pierwszej kolejności.",
  },

  discoverForm: {
    urlAriaLabel: "Adres strony",
    urlPlaceholder: "https://example.com",
    discoverButton: "Znajdź podstrony",
    maxPages: "Maks. podstron",
    maxPagesAria: "Maksymalna liczba podstron do wykrycia",
    maxDepth: "Maks. głębokość",
    maxDepthAria: "Maksymalna głębokość przeszukiwania",
    aiSummaryTitle: "Podsumowanie AI",
    aiSummaryDescription:
      "Otrzymaj zrozumiałe wyjaśnienie wyników audytu: ogólną kondycję strony, najważniejsze problemy i rekomendowane usprawnienia. Generowanie podsumowania AI trwa nieco dłużej i może zwiększyć koszt analizy.",
    aiSummaryNeedsKey: "Dodaj własny klucz API, aby to włączyć.",
    aiSummarySetupButton: "Skonfiguruj klucz API",
    aiSummaryManageButton: "Zarządzaj kluczem",
    aiSummaryActive: (provider: string, model: string) => `${provider} · ${model}`,
    validation: {
      urlRequired: "Adres URL jest wymagany",
      urlInvalid: "Podaj poprawny adres URL (np. https://example.com)",
      intWhole: "Musi być liczbą całkowitą",
      minPages: "Musi wynosić co najmniej 1",
      maxPages: "Nie może przekraczać 500",
      minDepth: "Musi wynosić 0 lub więcej",
      maxDepth: "Nie może przekraczać 3",
    },
  },

  apiKeyModal: {
    title: "Użyj własnego klucza API",
    subtitle:
      "Podsumowania AI działają na Twoim koncie LLM. Wybierz dostawcę i wklej klucz API — przetestujemy go przed zapisaniem.",
    providerLabel: "Dostawca",
    keyLabel: "Klucz API",
    modelLabel: "Model",
    priceLabel: "Cena za 1 mln tokenów",
    priceInput: "wej.",
    priceOutput: "wyj.",
    infoTitle: "Jak używamy Twojego klucza",
    infoPoints: [
      "Przechowywany wyłącznie w tej przeglądarce (localStorage) — nigdy na naszych serwerach.",
      "Wysyłany do naszego backendu tylko po to, by przekazać żądanie podsumowania wybranemu dostawcy.",
      "Podanie klucza odblokowuje podsumowanie AI; za użycie rozlicza Cię Twój dostawca.",
    ],
    guideTitle: "Jak zdobyć klucz",
    guideOpenLink: "Otwórz stronę kluczy",
    testButton: "Przetestuj i zapisz",
    testingButton: "Testowanie klucza…",
    cancelButton: "Anuluj",
    removeButton: "Usuń klucz",
    missingKey: "Najpierw wpisz klucz API.",
    success: (model: string) => `Klucz działa — podsumowania AI użyją modelu ${model}.`,
    failurePrefix: "Test klucza nie powiódł się:",
    guides: {
      openai: {
        steps: [
          "Zaloguj się na platform.openai.com/api-keys.",
          "Kliknij „Create new secret key” i skopiuj go.",
          "Upewnij się, że konto ma włączone płatności lub środki.",
        ],
      },
      gemini: {
        steps: [
          "Zaloguj się na aistudio.google.com/apikey kontem Google.",
          "Kliknij „Create API key” i skopiuj go.",
        ],
      },
      anthropic: {
        steps: [
          "Otwórz console.anthropic.com → Settings → API Keys.",
          "Kliknij „Create Key” i skopiuj go.",
          "Upewnij się, że konto ma środki.",
        ],
      },
      openrouter: {
        steps: [
          "Zaloguj się na openrouter.ai/keys.",
          "Utwórz klucz i skopiuj go.",
          "Dodaj środki do konta OpenRouter.",
        ],
      },
    },
  },

  idle: {
    awaitingInput: "Oczekiwanie na dane",
    description:
      "Podaj adres URL, aby rozpocząć. Najpierw przejdziemy po stronie i wykryjemy podstrony, a potem wybierzesz, które z nich poddać audytowi.",
  },

  errorView: {
    title: "Błąd",
    tryAgain: "Spróbuj ponownie",
  },

  progress: {
    maxSuffix: "maks.",
  },

  urlSelection: {
    discoveryComplete: (seconds: string) => `Wykrywanie zakończone — ${seconds}s`,
    foundPages: (count: number, host: string) =>
      `Znaleziono ${count} podstron w ${host}`,
    availableForAudit: (count: number) => `${count} dostępnych do audytu`,
    blockedSuffix: (count: number) => `, ${count} zablokowanych przez robots.txt`,
    failedSuffix: (count: number) => `, ${count} nie udało się pobrać`,
    crawlLimitReached: "· osiągnięto limit przeszukiwania — wyniki mogą być niepełne",
    rootFailed:
      "Nie udało się pobrać głównego adresu URL. Sprawdź, czy strona jest dostępna, i spróbuj ponownie.",
    selectPages: "Wybierz podstrony do audytu",
    selectAll: "Zaznacz wszystkie",
    deselectAll: "Odznacz wszystkie",
    depth: (depth: number) => `głębokość ${depth}`,
    robotsTxt: "robots.txt",
    fetchError: "błąd pobierania",
    runAudit: (pages: number, checks: number) =>
      `Uruchom audyt (${pages} podstron · ${checks} testów)`,
    startOver: "← Zacznij od nowa",
  },

  scope: {
    checksToRun: "Testy do wykonania",
    checks: {
      health: {
        label: "Kondycja",
        description: "Status HTTP, przekierowania, dostępność, TTFB",
      },
      seo: {
        label: "SEO",
        description: "Metatagi, nagłówki, canonical, dane strukturalne",
      },
      accessibility: {
        label: "Dostępność",
        description: "ARIA, teksty alternatywne, struktura nagłówków",
      },
      security: {
        label: "Bezpieczeństwo",
        description: "Nagłówki bezpieczeństwa HTTP",
      },
    },
  },

  report: {
    auditComplete: "AUDYT_ZAKOŃCZONY",
    health: "Kondycja",
    overallScore: "Wynik ogólny",
    scoreBreakdown: "Rozbicie wyniku",
    testResults: "Wyniki testów",
    discoverySummary: "Podsumowanie wykrywania",
    pagesDiscovered: "Wykryte podstrony",
    pagesAvailable: "Dostępne podstrony",
    blockedByRobots: "Zablokowane przez robots.txt",
    crawlDuration: "Czas przeszukiwania",
    sitemapFound: "Znaleziono mapę strony",
    robotsFetched: "Pobrano robots.txt",
    crawlLimitNote:
      "Osiągnięto limit przeszukiwania — część podstron mogła nie zostać wykryta.",
    pagesAudited: (count: number) => `Zaudytowane podstrony (${count})`,
    metrics: {
      ttfbDescription: "Time to First Byte — jak szybko odpowiada serwer.",
      seoDescription:
        "Wynik SEO na podstawie metatagów, nagłówków, canonical i danych strukturalnych.",
      a11yDescription:
        "Wynik dostępności z heurystyk HTML (etap 2 doda axe-core).",
    },
  },

  pageResult: {
    issues: (count: number) =>
      `${count} ${count === 1 ? "problem" : count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20) ? "problemy" : "problemów"}`,
    noIssues: "brak problemów",
    details: "Szczegóły",
    hide: "Ukryj",
    pageScore: "Wynik podstrony",
    health: "Kondycja",
    status: "Status",
    ttfb: "TTFB",
    redirectLoop: "Wykryto pętlę przekierowań",
    redirects: (count: number) =>
      `${count} ${count === 1 ? "przekierowanie" : count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20) ? "przekierowania" : "przekierowań"}`,
    seoScore: "Wynik SEO",
    a11yScore: "Wynik A11Y",
    securityScore: "Wynik bezpieczeństwa",
    seoIssues: "Problemy SEO",
    accessibilityIssues: "Problemy z dostępnością",
    securityFindings: "Wykrycia bezpieczeństwa",
  },

  seoDetails: {
    title: "Testy SEO",
    issuesHeading: (count: number) => `Problemy (${count})`,
    tooMany: (count: number) => `znaleziono ${count} (za dużo)`,
    chars: (count: number) => `${count} znaków`,
    imageCount: (count: number) => `${count} obraz(ów)`,
    robotsDefault: "Nie ustawiono (domyślnie: index, follow)",
    rows: {
      title: {
        label: "Tytuł strony",
        note: "Optymalna długość: 30–60 znaków. Wpływa na to, jak strona wygląda w wynikach wyszukiwania.",
      },
      description: {
        label: "Meta opis",
        note: "Optymalna długość: 120–160 znaków. Wyświetlany jako fragment w wynikach wyszukiwania.",
      },
      h1: {
        label: "Nagłówek H1",
        note: "Każda strona powinna mieć dokładnie jeden nagłówek H1 — główny temat strony.",
      },
      headings: {
        label: "Nagłówki H2 / H3",
        note: "Podnagłówki pomagają uporządkować treść dla czytelników i wyszukiwarek.",
      },
      canonical: {
        label: "Tag canonical",
        note: "Wskazuje wyszukiwarkom preferowany adres URL strony, zapobiegając problemom z duplikacją treści.",
      },
      schema: {
        label: "Dane strukturalne",
        note: "Dane strukturalne (JSON-LD) pomagają wyszukiwarkom zrozumieć treść strony i umożliwiają wzbogacone wyniki.",
      },
      images: {
        label: "Obrazy bez tekstu alternatywnego",
        note: "Atrybuty alt opisują obrazy czytnikom ekranu i są wykorzystywane przez wyszukiwarki.",
      },
      ogTitle: {
        label: "Tytuł OG",
        note: "Tytuł Open Graph decyduje o tym, jak wyświetla się tytuł strony przy udostępnianiu w mediach społecznościowych.",
      },
      ogDescription: {
        label: "Opis OG",
        note: "Opis Open Graph wyświetlany w podglądzie linku w mediach społecznościowych.",
      },
      ogImage: {
        label: "Obraz OG",
        note: "Obraz Open Graph wyświetlany przy udostępnianiu strony w mediach społecznościowych.",
      },
      robots: {
        label: "Meta robots",
        note: "Decyduje, czy wyszukiwarki mają indeksować tę stronę i podążać za jej linkami.",
      },
    },
    headingsValue: (h2: number, h3: number) => `${h2} H2, ${h3} H3`,
  },

  accessibilityDetails: {
    title: "Testy dostępności",
    auditScope: "Zakres audytu",
    rows: {
      lang: {
        label: "Atrybut języka HTML",
        note: "Element <html> musi mieć atrybut lang, aby czytniki ekranu wiedziały, jakiego języka użyć.",
      },
      alt: {
        label: "Tekst alternatywny obrazów",
        note: "Wszystkie elementy <img> muszą mieć atrybut alt. Czytniki ekranu odczytują go na głos, korzystają z niego też wyszukiwarki.",
      },
      label: {
        label: "Etykiety pól formularza",
        note: "Każde widoczne pole formularza musi mieć powiązaną etykietę lub aria-label, aby użytkownik wiedział, co wpisać.",
      },
      main: {
        label: "Punkt orientacyjny main",
        note: "Element <main> (lub role='main') pozwala użytkownikom klawiatury i czytników ekranu przejść od razu do głównej treści.",
      },
    },
  },

  healthDetails: {
    title: "Sprawdzenie kondycji",
    ttfbQuality: { excellent: "doskonały", good: "dobry", slow: "wolny" },
    statusLabels: {
      ok: "OK",
      redirect: "Przekierowanie",
      client_error: "Błąd klienta",
      server_error: "Błąd serwera",
      timeout: "Przekroczono czas",
      connection_error: "Błąd połączenia",
    },
    rows: {
      availability: {
        label: "Dostępność",
        note: "Strona odpowiada kodem HTTP 2xx lub 3xx",
      },
      status: {
        label: "Status HTTP",
        note: "Końcowy kod odpowiedzi po przejściu przekierowań",
      },
      ttfb: {
        label: "Time to First Byte",
        note: "Jak szybko serwer wysłał pierwszy bajt odpowiedzi. < 200 ms doskonale, < 800 ms dobrze, > 800 ms wolno.",
      },
      finalUrl: {
        label: "Końcowy adres URL",
        note: "Docelowy adres URL po wszystkich przekierowaniach",
      },
      redirects: {
        label: "Przekierowania",
        note: "Liczba przeskoków HTTP 3xx przed dotarciem do końcowego adresu URL. Łańcuchy dłuższe niż 3 przeskoki zwiększają opóźnienie.",
      },
    },
    redirectLoopDetected:
      "Wykryto pętlę przekierowań — łańcuch odwiedza ten sam adres URL więcej niż raz.",
    redirectChain: "Łańcuch przekierowań",
    errorPrefix: "Błąd",
  },

  securityDetails: {
    subScores: "Wyniki podkategorii bezpieczeństwa",
    criticalHigh: (count: number) => `Wykrycia krytyczne i wysokie (${count})`,
    evidence: "Dowód",
    noFrontendIssues: "✓ Nie znaleziono problemów bezpieczeństwa front-endu",
    noDependencyIssues: "✓ Nie znaleziono problemów z zależnościami",
    technologiesDetected: "Wykryte technologie",
    librariesDetected: "Wykryte biblioteki",
    subcategories: {
      headers: "Nagłówki",
      tls: "TLS",
      cookies: "Ciasteczka",
      dns: "DNS",
      frontend: "Front-end",
      dependencies: "Zależności",
      best_practices: "Dobre praktyki",
    },
    sections: {
      headers: "Nagłówki bezpieczeństwa HTTP",
      tls: "TLS / HTTPS",
      cookies: "Ciasteczka",
      dns: "Bezpieczeństwo DNS",
      frontend: "Bezpieczeństwo front-endu",
      dependencies: "Zależności JavaScript",
      bestPractices: "Dobre praktyki",
    },
    daysValue: (days: number) => `${days} dni`,
    foundValue: (count: number) => `znaleziono ${count}`,
    rows: {
      tlsVersion: {
        label: "Wersja TLS",
        note: "Wymagana jest wersja TLS 1.2 lub wyższa; preferowana TLS 1.3.",
      },
      certValid: {
        label: "Ważność certyfikatu",
        note: "Certyfikat musi być wystawiony przez zaufany urząd CA i nie może być przeterminowany.",
      },
      certExpiry: {
        label: "Wygaśnięcie certyfikatu",
        note: "Certyfikaty wygasające za mniej niż 30 dni należy odnowić.",
      },
      totalCookies: { label: "Łączna liczba ciasteczek", note: "" },
      spf: {
        label: "Rekord SPF",
        note: "Sender Policy Framework — zapobiega podszywaniu się pod nadawcę e-maili.",
      },
      dmarc: {
        label: "Rekord DMARC",
        note: "Domain-based Message Authentication — określa politykę dla nieudanych SPF/DKIM.",
      },
      dnssec: {
        label: "DNSSEC",
        note: "DNS Security Extensions — chroni przed fałszowaniem DNS.",
      },
      caa: {
        label: "Rekord CAA",
        note: "Certification Authority Authorization — ogranicza, które urzędy CA mogą wystawiać certyfikaty.",
      },
      securityTxt: {
        label: "security.txt",
        note: "Plik w formacie maszynowym, dzięki któremu badacze bezpieczeństwa mogą zgłaszać podatności.",
      },
      robotsTxt: {
        label: "robots.txt",
        note: "Wskazuje robotom, których ścieżek unikać. Ogranicza przypadkowe ujawnienie treści.",
      },
      sourceMaps: {
        label: "Ujawnione mapy źródeł",
        note: "Publiczne mapy źródeł ujawniają oryginalny kod źródłowy każdemu, kto je znajdzie.",
      },
    },
  },

  aiSummary: {
    heading: "Podsumowanie AI",
    generationFailed: "Nie udało się wygenerować podsumowania AI.",
    unaffectedNote: "Wyniki audytu powyżej są kompletne i pozostają bez zmian.",
    strengths: "Mocne strony",
    weaknesses: "Słabe strony",
    priorityRecommendations: "Priorytetowe rekomendacje",
    pagesNeedingAttention: "Podstrony wymagające uwagi",
    recommendedActions: "Zalecane działania",
  },
};
