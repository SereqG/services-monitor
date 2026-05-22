from __future__ import annotations

from typing import Any

# System prompt — kept verbatim from docs/ai_audit_summary_architecture_claude_prompt.md.
SYSTEM_PROMPT = """\
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

The user is not a developer."""

_PHASE1_INSTRUCTIONS = """\
Generate an overall summary of this website audit.

First, call the `audit_context_tool` with mode "general_info" to retrieve the curated \
audit context. Then respond with ONLY a JSON object — no markdown, no commentary — \
matching exactly this shape:

{
  "overall_assessment": "2-4 sentence plain-language verdict on the website's health",
  "main_strengths": ["short phrase", "..."],
  "main_weaknesses": ["short phrase", "..."],
  "priority_recommendations": ["actionable recommendation", "..."]
}

Base every statement on the retrieved data. Do not invent scores, grades or issues."""


def build_phase1_messages() -> list[dict[str, Any]]:
    """Messages for completion 1 — the overall website summary."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _PHASE1_INSTRUCTIONS},
    ]


def build_phase2_messages(problematic_urls: list[str]) -> list[dict[str, Any]]:
    """Messages for completion 2 — per-page analysis of the weakest pages."""
    url_lines = "\n".join(f"- {url}" for url in problematic_urls)
    content = f"""\
Analyze the weakest pages of this website audit.

For EACH page below, call `audit_context_tool` with mode "per_page_info" and that \
page's url to retrieve its curated data:
{url_lines}

Then respond with ONLY a JSON object — no markdown, no commentary — matching exactly \
this shape:

{{
  "problematic_pages": [
    {{
      "url": "the page url",
      "summary": "2-3 sentence plain-language explanation of what is weak on this page",
      "recommended_actions": ["actionable recommendation", "..."]
    }}
  ]
}}

Include exactly one entry per page listed above. Base every statement on the \
retrieved data. Do not invent scores or issues."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]
