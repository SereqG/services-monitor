# Service Monitor — Workflow Architecture Documentation for User Input Collection and Crawl Planning

## Purpose of This Document

This document provides a detailed explanation of the architectural decisions related to the first stage of the Service Monitor workflow, including:
- user input collection,
- input validation,
- discovery crawling,
- crawl scope planning,
- safety mechanisms,
- cost control,
- robots.txt compliance,
- protection against runaway crawling,
- UX architecture for page selection.

It explains:
- the decision-making process,
- pros and cons,
- technical implications,
- scalability considerations,
- future SaaS evolution impact.

---

# 1. Project Architecture Context

The Service Monitor project is designed as:
- workflow-oriented,
- audit-oriented,
- stateless MVP,
- future SaaS-ready.

The system is intended to:
- analyze websites,
- perform crawling,
- generate PDF reports,
- calculate quality scores,
- support future report comparison.

At the current stage:
- the system does not store report history,
- there is no persistent job metadata storage,
- cache reuse is not implemented,
- every crawl is executed from scratch.

---

# 2. Initial Input Model

Originally planned input fields:

## Required
- Root URL
- Email

## Optional
- Report name
- Subpage limit
- List of excluded subpages
- Max depth

---

# 3. Evolution of the Exclude List Architecture

Initially users were expected to manually provide:
- a list of URLs to exclude.

Example:

```txt
/admin
/checkout
/cart
```

This approach introduced:
- UX complexity,
- validation issues,
- parser complexity,
- potential ReDoS risks,
- canonicalization problems.

---

# 4. Final Decision — Discovery-Based Selection

The architecture was redesigned.

Instead of manual exclusion rules:
1. the system performs a discovery crawl,
2. collects the site structure,
3. presents a selectable UI,
4. allows users to select:
   - sections to analyze,
   - sections to exclude.

---

# 5. Discovery Phase as a Dedicated Subsystem

Discovery is not treated as:
- preprocessing,
- a minor crawler extension.

It is treated as:
- a dedicated architectural subsystem.

---

# 6. Discovery Engine Responsibilities

The Discovery Engine handles:
- URL discovery,
- URL classification,
- structure analysis,
- crawl risk analysis,
- crawl budget estimation.

It detects:
- infinite crawling,
- parameter explosions,
- calendar recursion,
- duplicate-heavy sections,
- faceted navigation.

---

# 7. Why Discovery Was Separated

## Cost Control
Without discovery:
- crawl size may explode,
- AI costs may become unmanageable,
- infrastructure may overload.

## Infrastructure Protection
Discovery allows:
- workload estimation,
- runaway crawl prevention,
- risk analysis.

## Better UX
Users:
- see the structure,
- understand scope,
- consciously select sections.

## SaaS Scalability
Discovery becomes the foundation for:
- pricing tiers,
- quotas,
- workload scheduling.

---

# 8. Final Workflow

## Stage A — User Input
- Root URL
- Email
- Report name

## Stage B — Discovery Crawl
- robots.txt fetch,
- discovery,
- structure building.

## Stage C — URL Selection
- user selects sections,
- user controls scope.

## Stage D — Final Crawl
- audit crawl,
- analysis,
- scoring,
- report generation.

---

# 9. URL Selection UI

Users should:
- not manually type URLs,
- only select sections from the generated structure.

Example:

```txt
☑ /
☑ /blog
☑ /about
☐ /products/*
```

---

# 10. URL Grouping

The system should:
- group similar URLs,
- simplify the structure.

Examples:

```txt
/products/*
/blog/*
```

Dynamic URLs:

```txt
/product/123
/product/456
```

→

```txt
/product/{id}
```

---

# 11. Include vs Exclude

The system should primarily use:
- INCLUDE-based UX.

Meaning:
“Which sections should be analyzed?”

Instead of:
“Which sections should be skipped?”

Benefits:
- safer crawl budgeting,
- simpler mental model,
- better UX.

---

# 12. Subpage Limits

Final decision:

```txt
default = 15
max = 50
```

Reasons:
- infrastructure protection,
- AI cost control,
- sufficient for MVP.

---

# 13. Max Depth Evolution

Initially:
- user-configurable.

Final decision:
- internal-only safety mechanism.

Configuration:

```txt
DEFAULT_MAX_DEPTH = 7
```

Depth still matters because:
- hidden recursive structures may exist,
- infinite hierarchies may appear,
- nested dynamic pages may occur.

---

# 14. Why Depth Should Not Be Exposed in UI

Most users:
- do not understand crawl depth,
- cannot choose proper values,
- could create invalid configurations.

Keeping it internal:
- simplifies UX,
- reduces friction.

---

# 15. Multi-Layer Crawl Protection

The crawler should implement:
- URL limits,
- depth limits,
- request limits,
- time limits,
- heuristics.

Heuristics should detect:
- pagination loops,
- calendar recursion,
- parameter explosions.

---

# 16. Discovery Hard Caps

Example:

```txt
max_urls_discovered = 500
max_depth = 3
max_duration = 120s
max_requests = 1000
```

Discovery itself must also remain protected.

---

# 17. Input Validation

## Root URL
Validation:
- valid format,
- HTTPS required,
- max 200 characters,
- no localhost,
- no private IPs,
- no dangerous schemes.

## Email
Validation:
- valid format,
- max 200 characters.

## Report Name
Validation:
- max 200 characters,
- sanitization,
- filesystem-safe.

---

# 18. SSRF Protection

The crawler must never access:
- localhost,
- private networks,
- internal infrastructure.

This is a critical security layer.

---

# 19. No Duplicate Detection

The system currently:
- does not store reports,
- does not reuse cache,
- does not detect repeated audits.

Reasons:
- simpler MVP,
- stateless architecture,
- no storage complexity.

Consequences:
- every crawl consumes full resources,
- limits become even more important.

---

# 20. robots.txt Policy

Final decision:

# The system always respects robots.txt

This applies to:
- discovery crawl,
- final crawl,
- URL selection UI.

Blocked URLs:
- are not analyzed,
- are not crawled,
- are not selectable.

---

# 21. Centralized Robots Policy Engine

Recommended architecture:

```txt
RobotsPolicyService
```

Benefits:
- consistency,
- centralized logic,
- fewer edge cases.

---

# 22. User-Agent

The crawler should use a dedicated user-agent:

```txt
ServiceMonitorBot/1.0
```

This is more transparent and professional.

---

# 23. robots.txt and UX

Blocked sections should:
- be hidden,
- or visibly marked as blocked.

Reports should include:
- crawl limitation sections.

---

# 24. Sitemap Discovery

After robots.txt fetch:
- sitemap.xml should be automatically detected.

Benefits:
- better coverage,
- faster discovery,
- improved structure detection.

---

# 25. Final Architectural Philosophy

The system should:
- control costs,
- remain defensive,
- simplify UX,
- reduce runaway crawl risk,
- stay transparent,
- remain scalable.

---

# 26. Most Important Architectural Decisions

- Discovery as a dedicated subsystem
- Include-based URL selection
- Hard crawl limits
- Internal-only max depth
- Centralized robots policy
- Stateless MVP architecture

---

# 27. Strategic Summary

The entire architecture was designed around:
- cost control,
- infrastructure stability,
- UX simplicity,
- future SaaS scalability.

It prepares the foundation for:
- pricing,
- quotas,
- recurring audits,
- report comparison,
- trend analysis.

---

# 28. Final Recommended Architecture

```txt
User Input
↓
Robots Fetch
↓
Discovery Crawl
↓
Risk Analysis
↓
URL Classification
↓
Selection UI
↓
Final Crawl
↓
AI Analysis
↓
Scoring
↓
PDF Report
```
