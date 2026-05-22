# Project Overview

A deterministic service monitoring and auditing platform that analyzes services/websites, collects structured audit data, generates reports and scores, tracks historical changes, and exports structured data.

**Priorities:** transparency, deterministic processing, modular architecture, maintainability, scalability, explicit business logic.

All reports, calculations, scores, comparisons, and recommendations MUST be traceable, explainable, reproducible, and derived from verifiable data. Never use hidden business logic, opaque scoring, or implicit architecture.

---

# Tech Stack

## Backend
- Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, httpx, pytest

## Frontend
- Next.js, TypeScript, App Router, TailwindCSS, shadcn/ui, TanStack Query, Zod

## Testing
- pytest, Playwright

---

# Monorepo Structure

```
/apps
  /api
  /web
/packages
  /shared       # small, stable, domain-agnostic only
  /contracts
  /ui
/docs
```

Applications and domains MUST remain clearly separated. Business logic MUST NOT be moved into shared utilities prematurely.

---

# Documentation Rules

`docs/` is the primary source of truth for architecture, workflows, business rules, scoring logic, and implementation decisions.

Before implementing any feature Claude MUST:
1. Search `docs/` for related documentation
2. Read relevant markdown files
3. Follow documented architecture and constraints
4. Ask if documentation is unclear or contradictory

If implementation behavior changes, relevant docs MUST be updated. If docs conflict with implementation, Claude MUST stop and ask for clarification.

---

# Vertical Slice Architecture

Each feature/domain is an isolated slice owning: business rules, application flow, contracts, validation, infrastructure integration, and tests.

Avoid: god services, large shared managers, cross-slice coupling, shared mutable state, business logic in utils/helpers.

---

# Engineering Principles

Prefer: explicit code, deterministic behavior, small focused modules, composition over inheritance, pure functions, strong typing, readable over clever.

Avoid: hidden side effects, premature abstractions, unnecessary indirection, large classes, deeply nested logic, implicit behavior, magic values.

Every abstraction must justify its existence. No speculative architecture or generic frameworks for hypothetical futures.

---

# Coding Standards

Claude SHOULD: use descriptive naming, keep functions focused, keep files small, prefer explicit interfaces, use strong typing, separate orchestration from domain logic.

Claude MUST NOT: leave dead code, leave commented-out code, create hidden coupling, introduce undocumented behavior, silently change public contracts.

**Backend:** async I/O, explicit schemas, Pydantic validation, service boundaries, typed responses. No fat controllers, no business logic in routes.

**Frontend:** server-safe architecture, isolated UI components, typed API contracts, predictable state, explicit loading/error states. No deeply coupled components, no duplicated business logic.

---

# Testing Rules

Tests are mandatory. Every new feature MUST include unit tests and integration tests where applicable. Critical user flows MUST have Playwright e2e tests. Bug fixes MUST include regression tests.

Tests MUST be: deterministic, isolated, readable, maintainable, meaningful.

Avoid: flaky tests, implementation-detail assertions, unnecessary mocks, snapshot abuse.

---

# AI & Automation Rules

AI MUST remain: explainable, traceable, deterministic whenever possible.

AI MAY: summarize data, classify content, assist analysis, generate recommendations.

AI MUST NOT: generate hidden scoring logic, silently modify results, bypass validation, become the source of truth, introduce non-reproducible behavior.

All AI-generated outputs must be reviewable and auditable.

---

# Security & Validation Rules

All external data MUST be treated as untrusted.

Claude MUST: validate all input, sanitize URLs, handle failures explicitly, respect robots.txt, avoid unsafe parsing.

Avoid: silent failures, swallowed exceptions, unsafe deserialization, hidden retries without visibility.

---

# Reporting & Data Integrity

Reports MUST be: reproducible, explainable, auditable, deterministic, traceable to source data.

Missing or partial data MUST be explicit and MUST NOT silently affect scoring. Scores MUST expose reasoning and avoid hidden weighting.

Exports support: PDF, JSON, CSV.

---

# Decision-Making Process

Claude MUST ask questions when: requirements are ambiguous, business logic is unclear, docs conflict, multiple valid implementations exist, architecture changes are required, shared modules are affected, dependencies must be added, or behavior changes may affect other slices.

Claude MUST NOT guess unclear requirements.

---

# Architecture & Refactoring Rules

Large architectural changes REQUIRE: implementation plan, reasoning, tradeoff analysis, risk explanation, and approval before implementation.

Claude MAY refactor, reorganize slices, introduce new modules, create migrations, or update docs — BUT ONLY after explaining why, expected benefits, risks, and impact. Prefer incremental refactoring. Avoid broad rewrites unless explicitly approved.

---

# Dependency Rules

New dependencies MUST solve a real problem, align with architecture, and remain maintainable. Before adding, Claude MUST explain why it's needed, alternatives considered, and long-term maintenance implications.

---

# Observability & Error Handling

Prefer: structured logging, typed errors, explicit failure handling, observable workflows.

Avoid: silent retries, swallowed exceptions, hidden fallback behavior, untraceable processing.

---

# Workflow

Before implementing, Claude SHOULD:
1. Read relevant documentation
2. Understand the existing slice
3. Analyze existing patterns
4. Ask clarification questions if needed
5. Propose implementation approach
6. Implement incrementally
7. Add/update tests
8. Update documentation
9. Verify compatibility and consistency

---

# Claude Responsibilities

MUST: follow documented architecture, respect project conventions, prefer minimal safe changes, maintain slice isolation, create tests, update documentation, explain tradeoffs, ask when uncertain.

MUST NOT: invent undocumented business rules, bypass architecture rules, introduce unnecessary abstractions, refactor unrelated code, ignore documentation, silently change behavior, introduce hidden complexity.
