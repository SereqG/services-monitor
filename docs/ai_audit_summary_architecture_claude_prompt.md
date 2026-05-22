# AI Audit Summary Architecture — Claude Code Implementation Guide

## Project Context

This document describes the proposed AI architecture for the website audit platform.

The goal is to implement an AI-powered audit explanation layer that:
- explains audit results to non-technical users,
- minimizes LLM costs,
- reduces latency,
- avoids hallucinations,
- uses deterministic preprocessing,
- scales efficiently,
- keeps AI isolated from the core audit engine.

The AI system is NOT responsible for performing the audit itself.

The audit engine remains fully deterministic.

AI is used only as an interpretation and explanation layer.

---

# Core Principles

## 1. AI Must Be Optional

The user should explicitly decide whether AI analysis is enabled.

This decision should happen at the beginning of the workflow.

### Why

Benefits:
- lower processing cost,
- faster report generation,
- deterministic output without AI,
- better scalability,
- avoids unnecessary LLM usage.

### UX Recommendation

#### Toggle Label

AI-Powered Summary

#### Description

Get a simplified explanation of your audit results, including:
- overall website health,
- key problems,
- recommended improvements,
- detailed analysis of weaker pages.

AI summaries take slightly longer to generate and may increase processing cost.

---

# High-Level Architecture

```text
AuditReport
    ↓
AI Preprocessing Layer
    ↓
AiAnalysisDataset
    ↓
Deterministic Retrieval Tool
    ↓
Controlled LLM Orchestration
    ↓
Structured AI Response
```

---

# Critical Architectural Rule

## NEVER send the entire AuditReport JSON to the LLM

This is extremely important.

The raw audit JSON:
- is too large,
- contains too much noise,
- increases token cost,
- reduces response quality,
- increases hallucination risk,
- creates unstable outputs.

The LLM should ONLY receive:
- aggregated metrics,
- curated insights,
- deterministic summaries,
- problematic page data,
- simplified issue lists.

---

# AI Architecture Overview

The AI system should use a multi-layer architecture.

## Layer 1 — Raw Audit Engine

Produces:

```python
AuditReport
```

The raw audit remains the source of truth.

---

## Layer 2 — AI Preprocessing Layer

Transforms:
- AuditReport
into:
- AiAnalysisDataset

This layer is deterministic.

No AI should be used here.

Responsibilities:
- aggregate scores,
- calculate averages,
- detect weak pages,
- extract common issues,
- rank findings,
- reduce noise,
- optimize context for AI.

---

## Layer 3 — AI Dataset Storage

The processed AI dataset should be stored as JSON.

Example:

```text
storage/ai_context/{audit_id}.json
```

The dataset should be:
- overwritten per audit,
- temporary,
- lightweight,
- AI-focused.

This is NOT a cache of the full audit.

It is an optimized AI context dataset.

---

## Layer 4 — Deterministic Retrieval Tool

The LLM should NOT directly access raw JSON.

Instead, it should use a deterministic retrieval tool.

The tool:
- fetches curated data,
- limits context size,
- ensures stable prompts,
- minimizes noise.

This behaves similarly to a lightweight RAG system, but WITHOUT embeddings or vector search.

---

# Proposed AI Dataset Structure

```json
{
  "version": "1.0",
  "general_info": {
    "overall_score": 72,
    "grade": "C",
    "categories": {
      "seo": {
        "average_score": 61,
        "consistency": 74,
        "common_issues": [
          "Missing meta descriptions",
          "Multiple H1 headings"
        ]
      }
    },
    "priority_areas": [
      "accessibility",
      "seo"
    ]
  }
}
```

---

# AI Retrieval Tool Design

## Tool Name

```text
audit_context_tool
```

---

# Supported Modes

## Mode: general_info

Returns:
- overall score,
- category summaries,
- consistency metrics,
- global issue trends,
- priority areas,
- problematic page ranking.

---

## Mode: per_page_info

Returns:
- single-page analysis,
- category scores,
- issue summaries,
- prioritized recommendations.

---

# Deterministic Preprocessing

The preprocessing layer is the most important component of the AI system.

LLMs should NEVER:
- calculate averages,
- detect outliers,
- rank pages,
- aggregate issues,
- determine priorities.

All analytics must happen deterministically in backend code.

The LLM only:
- explains,
- summarizes,
- prioritizes,
- simplifies language.

---

# Consistency Metric

A consistency metric should be introduced.

Purpose:
- measure how stable scores are across pages.

Example:

Site A:
68, 71, 69, 72

Site B:
10, 100, 20, 90

### Proposed Formula

```python
consistency = 100 - standard_deviation(scores)
```

Higher variance:
- lower consistency.

---

# Problematic Pages Algorithm

## Step 1 — Calculate Global Averages

```python
global_seo_avg
global_accessibility_avg
global_health_avg
```

## Step 2 — Calculate Weakness Score

```python
weakness_score = (
    max(0, global_seo_avg - page.seo.score) +
    max(0, global_accessibility_avg - page.accessibility.score)
)
```

## Step 3 — Sort Descending

Worst pages first.

## Step 4 — Limit Results

```python
problematic_pages[:10]
```

Maximum:
- 10 pages.

---

# Recommended Orchestration Flow

## Step 1

Fetch:
- general_info

## Step 2

Generate:
- overall website summary.

## Step 3

Fetch:
- top problematic pages.

## Step 4

Generate:
- per-page analysis.

---

# Recommended Optimization

Use TWO separate LLM calls.

## Completion 1 — Overall Summary

Input:
- general_info

## Completion 2 — Weak Pages Analysis

Input:
- problematic pages only.

Benefits:
- smaller context windows,
- lower token cost,
- improved focus,
- easier retries,
- easier caching.

---

# AI Output Requirements

The AI output must:
- use simple English,
- avoid technical jargon,
- explain concepts clearly,
- focus on non-technical users,
- remain educational,
- remain actionable.

The target user is NOT a developer.

---

# Recommended System Prompt

```text
You are an AI assistant that explains website audit results to non-technical users.

Your task is to:
- explain problems in simple language,
- avoid technical jargon,
- clearly describe why issues matter,
- suggest practical improvements,
- prioritize the most important issues,
- keep the tone friendly and professional.

Do not use advanced technical language unless necessary.
Always explain technical concepts in simple terms.

Focus on:
- clarity,
- readability,
- actionable advice.

The user is not a developer.
```

---

# Structured AI Output

The response must follow a strict schema.

```json
{
  "summary": {
    "overall_assessment": "...",
    "main_strengths": [],
    "main_weaknesses": [],
    "priority_recommendations": []
  },
  "problematic_pages": [
    {
      "url": "...",
      "summary": "...",
      "recommended_actions": []
    }
  ]
}
```

---

# Suggested Backend Module Structure

```text
slices/ai_summary/
├── service.py
├── preprocessing.py
├── prompt_builder.py
├── schemas.py
├── llm_client.py
├── transformers.py
└── retrieval_tool.py
```

---

# Recommended Model

## Provider

OpenRouter

## Model

google/gemini-2.5-flash

Benefits:
- low cost,
- fast inference,
- good structured JSON understanding,
- excellent summarization performance,
- strong price/performance ratio.

---

# Final Architectural Philosophy

The AI system should behave as:
- an explanation layer,
- an educational assistant,
- a prioritization system.

It should NOT:
- perform calculations,
- analyze raw data,
- replace deterministic audit logic.

The backend remains authoritative.

AI only translates technical results into human-friendly explanations.

---

# Implementation Notes

This section records how the architecture above was actually implemented, including
deviations from the original proposal.

## Module layout

Implemented under `apps/api/slices/ai_summary/`:

```
slices/ai_summary/
├── schemas.py          AiAnalysisDataset, AiSummary + nested models
├── preprocessing.py    AuditReport → AiAnalysisDataset (deterministic)
├── storage.py          write/read storage/ai_context/{audit_id}.json
├── retrieval_tool.py   audit_context_tool (general_info / per_page_info)
├── prompt_builder.py   system prompt + phase-1/phase-2 messages
├── llm_client.py       raw-httpx OpenRouter chat-completions + tool loop
├── transformers.py     LLM JSON → validated AiSummary
└── service.py          generate_ai_summary + safe_generate_ai_summary
```

There is no `router.py` — the feature is inline in the audit flow, not a standalone
endpoint.

## Trigger and integration

- `AuditRequest.enable_ai_summary: bool` (default `false`) opts a single audit in.
- AI runs as the final step of `run_audit` / `stream_audit`, after the deterministic
  report is assembled. The result is attached as `AuditReport.ai_summary`.
- Every audit generates an `audit_id = uuid.uuid4().hex`, set on `AuditReport.audit_id`,
  regardless of whether AI is enabled.

## Storage

The curated `AiAnalysisDataset` is written to `storage/ai_context/{audit_id}.json`
(overwritten per audit). The directory is configurable via `AI_STORAGE_DIR` and is
gitignored. This is the first persistence in the app — a lightweight AI-context store,
not the application database.

## Retrieval tool

`audit_context_tool` is exposed to the LLM as an OpenRouter function tool with modes
`general_info` and `per_page_info`. `audit_id` is **not** a tool parameter — it is bound
server-side per audit so the model cannot point the tool at a different dataset. The tool
never raises: failures are returned as `{"error": ...}` so the model can recover.

## LLM calls

- Provider: OpenRouter, called with raw `httpx` (no SDK dependency added).
- Model: `google/gemini-2.5-flash` (configurable via `AI_SUMMARY_MODEL`).
- Two completions: (1) overall summary from `general_info`, (2) weak-page analysis from
  `per_page_info`. Each runs a bounded tool-call loop.
- One retry per completion on transient failures (network error, HTTP 429/5xx). Auth
  (401/403) and other 4xx errors are terminal.

## Configuration

`apps/api/core/config.py` / `.env`:

- `OPENROUTER_API_KEY` — required for AI; absent ⇒ AI is reported as not configured.
- `AI_SUMMARY_ENABLED` — server-wide kill switch (default `true`).
- `AI_SUMMARY_MODEL`, `AI_SUMMARY_TIMEOUT_SECONDS`, `AI_SUMMARY_MAX_TOKENS`,
  `AI_SUMMARY_MAX_TOOL_ITERATIONS`, `AI_STORAGE_DIR`.

## Failure contract

`AiSummary.status` is `"ok"` or `"error"`. `safe_generate_ai_summary` wraps generation so
that **no AI failure ever breaks an audit** — a failure yields `status="error"` with an
explicit `error` message and a full, valid deterministic report. AI output never feeds
back into scoring.

