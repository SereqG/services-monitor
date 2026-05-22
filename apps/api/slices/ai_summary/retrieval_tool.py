from __future__ import annotations

from typing import Any

from core.exceptions import AiSummaryError
from core.logging import logger
from slices.ai_summary import storage

TOOL_NAME = "audit_context_tool"

# OpenRouter / OpenAI-compatible function-tool definition. `audit_id` is NOT a
# parameter — it is bound server-side per audit so the model cannot pick a dataset.
TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": TOOL_NAME,
        "description": (
            "Fetch curated, pre-computed website audit context. Returns only "
            "aggregated metrics and curated insights — never raw audit data. "
            "Use mode='general_info' for the overall audit picture, and "
            "mode='per_page_info' with a 'url' for a single problematic page."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["general_info", "per_page_info"],
                    "description": "Which slice of audit context to retrieve.",
                },
                "url": {
                    "type": "string",
                    "description": "Page URL — required when mode='per_page_info'.",
                },
            },
            "required": ["mode"],
        },
    },
}


def run_audit_context_tool(
    audit_id: str, mode: str, url: str | None = None
) -> dict[str, Any]:
    """Deterministic retrieval tool over the stored AI dataset.

    Never raises — failures are returned as a compact ``{"error": ...}`` dict so
    the LLM tool-call loop can recover and still produce a (degraded) answer.
    """
    logger.info(
        "function=run_audit_context_tool | audit_id=%s mode=%s url=%s",
        audit_id,
        mode,
        url,
    )
    try:
        dataset = storage.read_dataset(audit_id)
    except AiSummaryError as exc:
        return {"error": exc.message}

    if mode == "general_info":
        return dataset.general_info.model_dump()

    if mode == "per_page_info":
        if not url:
            return {"error": "Parameter 'url' is required when mode='per_page_info'."}
        for page in dataset.general_info.problematic_pages:
            if page.url == url:
                return page.model_dump()
        return {"error": f"No problematic-page data for url {url!r}."}

    return {"error": f"Unknown mode {mode!r}. Use 'general_info' or 'per_page_info'."}
