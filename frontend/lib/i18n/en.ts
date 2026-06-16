// English UI dictionary — the canonical shape. `pl.ts` must satisfy `Dictionary`,
// so every key here is guaranteed to exist in Polish too (no missing-key fallback
// needed). Parameterized strings are functions for type-safe interpolation.

export const en = {
  language: {
    label: "Language",
    en: "EN",
    pl: "PL",
    enName: "English",
    plName: "Polski",
  },

  common: {
    missing: "Missing",
    present: "Present",
    none: "None",
    noneFound: "None found",
    yes: "Yes",
    no: "No",
    unknown: "Unknown",
    valid: "Valid",
    invalid: "Invalid",
    enabled: "Enabled",
    disabled: "Disabled",
    available: "Available",
    unavailable: "Unavailable",
    na: "N/A",
    pass: "Pass",
    unexpectedError: "An unexpected error occurred.",
  },

  severity: {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low",
    info: "info",
    informational: "informational",
    serious: "serious",
    moderate: "moderate",
    minor: "minor",
  } as Record<string, string>,

  categories: {
    health: "Health",
    performance: "Performance",
    seo: "SEO",
    accessibility: "Accessibility",
    security: "Security",
  } as Record<string, string>,

  home: {
    engineOnline: "Engine online",
    heroTitle: "Analyze web performance in real time.",
    heroSubtitle:
      "Paste a URL and we'll crawl the site, then run a full audit covering SEO, accessibility, and health — then translate the numbers into plain language so you know what to fix first.",
  },

  discoverForm: {
    urlAriaLabel: "Website URL",
    urlPlaceholder: "https://example.com",
    discoverButton: "Discover pages",
    maxPages: "Max pages",
    maxPagesAria: "Max pages to discover",
    maxDepth: "Max depth",
    maxDepthAria: "Max crawl depth",
    aiSummaryTitle: "AI-Powered Summary",
    aiSummaryDescription:
      "Get a simplified explanation of your audit results, including overall website health, key problems, and recommended improvements. AI summaries take slightly longer to generate and may increase processing cost.",
    aiSummaryNeedsKey: "Add your own AI API key to enable this.",
    aiSummarySetupButton: "Set up API key",
    aiSummaryManageButton: "Manage key",
    aiSummaryActive: (provider: string, model: string) => `${provider} · ${model}`,
    validation: {
      urlRequired: "URL is required",
      urlInvalid: "Must be a valid URL (e.g. https://example.com)",
      intWhole: "Must be a whole number",
      minPages: "Must be at least 1",
      maxPages: "Cannot exceed 500",
      minDepth: "Must be 0 or greater",
      maxDepth: "Cannot exceed 3",
    },
  },

  apiKeyModal: {
    title: "Use your own AI API key",
    subtitle:
      "AI summaries run on your own LLM account. Pick a provider and paste an API key — we test it before saving.",
    providerLabel: "Provider",
    keyLabel: "API key",
    modelLabel: "Model",
    priceLabel: "Price per 1M tokens",
    priceInput: "in",
    priceOutput: "out",
    infoTitle: "How your key is used",
    infoPoints: [
      "Stored only in this browser (localStorage) — never on our servers.",
      "Sent to our backend only to relay the summary request to your chosen provider.",
      "Providing a key unlocks the AI summary; your provider bills you for usage.",
    ],
    guideTitle: "How to get a key",
    guideOpenLink: "Open key page",
    testButton: "Test & save",
    testingButton: "Testing key…",
    cancelButton: "Cancel",
    removeButton: "Remove key",
    missingKey: "Enter an API key first.",
    success: (model: string) => `Key works — AI summaries will use ${model}.`,
    failurePrefix: "Key test failed:",
    guides: {
      openai: {
        steps: [
          "Sign in at platform.openai.com/api-keys.",
          "Click “Create new secret key” and copy it.",
          "Make sure your account has billing or credits enabled.",
        ],
      },
      gemini: {
        steps: [
          "Sign in at aistudio.google.com/apikey with your Google account.",
          "Click “Create API key” and copy it.",
        ],
      },
      anthropic: {
        steps: [
          "Open console.anthropic.com → Settings → API Keys.",
          "Click “Create Key” and copy it.",
          "Make sure your account has credits.",
        ],
      },
      openrouter: {
        steps: [
          "Sign in at openrouter.ai/keys.",
          "Create a key and copy it.",
          "Add credits to your OpenRouter account.",
        ],
      },
    },
  },

  idle: {
    awaitingInput: "Awaiting input",
    description:
      "Enter a URL to begin. We'll first crawl the site to discover pages, then you can choose which ones to audit.",
  },

  errorView: {
    title: "Error",
    tryAgain: "Try again",
  },

  progress: {
    maxSuffix: "max",
  },

  urlSelection: {
    discoveryComplete: (seconds: string) => `Discovery complete — ${seconds}s`,
    foundPages: (count: number, host: string) => `Found ${count} pages on ${host}`,
    availableForAudit: (count: number) => `${count} available for audit`,
    blockedSuffix: (count: number) => `, ${count} blocked by robots.txt`,
    failedSuffix: (count: number) => `, ${count} failed to fetch`,
    crawlLimitReached: "· crawl limit reached — results may be incomplete",
    rootFailed:
      "The root URL could not be fetched. Check that the site is reachable and try again.",
    selectPages: "Select pages to audit",
    selectAll: "Select all",
    deselectAll: "Deselect all",
    depth: (depth: number) => `depth ${depth}`,
    robotsTxt: "robots.txt",
    fetchError: "fetch error",
    runAudit: (pages: number, checks: number) =>
      `Run audit (${pages} pages · ${checks} checks)`,
    startOver: "← Start over",
  },

  scope: {
    checksToRun: "Checks to run",
    checks: {
      health: {
        label: "Health",
        description: "HTTP status, redirects, availability, TTFB",
      },
      seo: {
        label: "SEO",
        description: "Meta tags, headings, canonical, structured data",
      },
      accessibility: {
        label: "Accessibility",
        description: "ARIA, alt text, heading structure",
      },
      security: {
        label: "Security",
        description: "HTTP security response headers",
      },
    },
  },

  report: {
    auditComplete: "AUDIT_COMPLETE",
    health: "Health",
    overallScore: "Overall score",
    scoreBreakdown: "Score breakdown",
    testResults: "Test results",
    discoverySummary: "Discovery summary",
    pagesDiscovered: "Pages discovered",
    pagesAvailable: "Pages available",
    blockedByRobots: "Blocked by robots.txt",
    crawlDuration: "Crawl duration",
    sitemapFound: "Sitemap found",
    robotsFetched: "Robots.txt fetched",
    crawlLimitNote: "Crawl limit reached — some pages may not have been discovered.",
    pagesAudited: (count: number) => `Pages audited (${count})`,
    metrics: {
      ttfbDescription: "Time to First Byte — how fast the server responds.",
      seoDescription:
        "SEO score based on meta tags, headings, canonical, and structured data.",
      a11yDescription:
        "Accessibility score from HTML heuristics (Phase 2 adds axe-core).",
    },
  },

  pageResult: {
    issues: (count: number) => `${count} ${count !== 1 ? "issues" : "issue"}`,
    noIssues: "no issues",
    details: "Details",
    hide: "Hide",
    pageScore: "Page score",
    health: "Health",
    status: "Status",
    ttfb: "TTFB",
    redirectLoop: "Redirect loop detected",
    redirects: (count: number) => `${count} ${count !== 1 ? "redirects" : "redirect"}`,
    seoScore: "SEO score",
    a11yScore: "A11Y score",
    securityScore: "Security score",
    seoIssues: "SEO issues",
    accessibilityIssues: "Accessibility issues",
    securityFindings: "Security findings",
  },

  seoDetails: {
    title: "SEO checks",
    issuesHeading: (count: number) => `Issues (${count})`,
    tooMany: (count: number) => `${count} found (too many)`,
    chars: (count: number) => `${count} chars`,
    imageCount: (count: number) => `${count} image(s)`,
    robotsDefault: "Not set (default: index, follow)",
    rows: {
      title: {
        label: "Page title",
        note: "Optimal length: 30–60 chars. Affects how the page appears in search results.",
      },
      description: {
        label: "Meta description",
        note: "Optimal length: 120–160 chars. Shown as the snippet in search results.",
      },
      h1: {
        label: "H1 heading",
        note: "Every page should have exactly one H1 — the primary topic of the page.",
      },
      headings: {
        label: "H2 / H3 headings",
        note: "Subheadings help structure content for readers and search engines.",
      },
      canonical: {
        label: "Canonical tag",
        note: "Tells search engines the preferred URL for this page, preventing duplicate-content issues.",
      },
      schema: {
        label: "Schema markup",
        note: "Structured data (JSON-LD) helps search engines understand page content and enables rich results.",
      },
      images: {
        label: "Images without alt text",
        note: "Alt attributes describe images for screen readers and are used by search engines.",
      },
      ogTitle: {
        label: "OG title",
        note: "Open Graph title controls how the page title appears when shared on social media.",
      },
      ogDescription: {
        label: "OG description",
        note: "Open Graph description shown in social media link previews.",
      },
      ogImage: {
        label: "OG image",
        note: "Open Graph image displayed when the page is shared on social media.",
      },
      robots: {
        label: "Robots meta",
        note: "Controls whether search engines should index this page and follow its links.",
      },
    },
    headingsValue: (h2: number, h3: number) => `${h2} H2, ${h3} H3`,
  },

  accessibilityDetails: {
    title: "Accessibility checks",
    auditScope: "Audit scope",
    rows: {
      lang: {
        label: "HTML language attribute",
        note: "The <html> element must have a lang attribute so screen readers know which language to use.",
      },
      alt: {
        label: "Image alt text",
        note: "All <img> elements must have an alt attribute. Screen readers read it aloud; search engines use it too.",
      },
      label: {
        label: "Form input labels",
        note: "Every visible form input must have an associated label or aria-label so users know what to type.",
      },
      main: {
        label: "Main landmark",
        note: "A <main> element (or role='main') lets keyboard and screen reader users skip directly to the main content.",
      },
    },
  },

  healthDetails: {
    title: "Health check",
    ttfbQuality: { excellent: "excellent", good: "good", slow: "slow" },
    statusLabels: {
      ok: "OK",
      redirect: "Redirect",
      client_error: "Client error",
      server_error: "Server error",
      timeout: "Timeout",
      connection_error: "Connection error",
    } as Record<string, string>,
    rows: {
      availability: {
        label: "Availability",
        note: "Site responds with HTTP 2xx or 3xx",
      },
      status: {
        label: "HTTP status",
        note: "Final response code after following redirects",
      },
      ttfb: {
        label: "Time to First Byte",
        note: "How fast the server sent the first response byte. < 200ms excellent, < 800ms good, > 800ms slow.",
      },
      finalUrl: {
        label: "Final URL",
        note: "Destination URL after all redirects",
      },
      redirects: {
        label: "Redirects",
        note: "Number of HTTP 3xx hops before reaching the final URL. Chains longer than 3 hops add latency.",
      },
    },
    redirectLoopDetected:
      "Redirect loop detected — the chain visits the same URL more than once.",
    redirectChain: "Redirect chain",
    errorPrefix: "Error",
  },

  securityDetails: {
    subScores: "Security subcategory scores",
    criticalHigh: (count: number) => `Critical & high findings (${count})`,
    evidence: "Evidence",
    noFrontendIssues: "✓ No frontend security issues found",
    noDependencyIssues: "✓ No dependency issues found",
    technologiesDetected: "Technologies detected",
    librariesDetected: "Libraries detected",
    subcategories: {
      headers: "Headers",
      tls: "TLS",
      cookies: "Cookies",
      dns: "DNS",
      frontend: "Frontend",
      dependencies: "Dependencies",
      best_practices: "Best Practices",
    } as Record<string, string>,
    sections: {
      headers: "HTTP security headers",
      tls: "TLS / HTTPS",
      cookies: "Cookies",
      dns: "DNS security",
      frontend: "Frontend security",
      dependencies: "JavaScript dependencies",
      bestPractices: "Best practices",
    },
    daysValue: (days: number) => `${days} days`,
    foundValue: (count: number) => `${count} found`,
    rows: {
      tlsVersion: {
        label: "TLS version",
        note: "TLS 1.2 or higher is required; TLS 1.3 is preferred.",
      },
      certValid: {
        label: "Certificate valid",
        note: "Certificate must be issued by a trusted CA and not expired.",
      },
      certExpiry: {
        label: "Certificate expiry",
        note: "Certificates expiring in less than 30 days should be renewed.",
      },
      totalCookies: { label: "Total cookies", note: "" },
      spf: {
        label: "SPF record",
        note: "Sender Policy Framework — prevents email spoofing.",
      },
      dmarc: {
        label: "DMARC record",
        note: "Domain-based Message Authentication — defines policy for failed SPF/DKIM.",
      },
      dnssec: {
        label: "DNSSEC",
        note: "DNS Security Extensions — protects against DNS spoofing.",
      },
      caa: {
        label: "CAA record",
        note: "Certification Authority Authorization — restricts which CAs can issue certificates.",
      },
      securityTxt: {
        label: "security.txt",
        note: "A machine-readable file for security researchers to report vulnerabilities.",
      },
      robotsTxt: {
        label: "robots.txt",
        note: "Tells crawlers which paths to avoid. Reduces accidental exposure.",
      },
      sourceMaps: {
        label: "Source maps exposed",
        note: "Public source maps expose original source code to anyone who looks.",
      },
    },
  },

  aiSummary: {
    heading: "AI summary",
    generationFailed: "The AI summary could not be generated.",
    unaffectedNote: "Your audit results above are complete and unaffected.",
    strengths: "Strengths",
    weaknesses: "Weaknesses",
    priorityRecommendations: "Priority recommendations",
    pagesNeedingAttention: "Pages needing attention",
    recommendedActions: "Recommended actions",
  },
};

export type Dictionary = typeof en;
