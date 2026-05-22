from __future__ import annotations

from typing import Any

import httpx

from core.exceptions import AiSummaryError
from core.logging import logger
from slices.ai_summary import storage
from slices.ai_summary.llm_client import ToolHandler, run_completion
from slices.ai_summary.preprocessing import build_ai_dataset
from slices.ai_summary.prompt_builder import build_phase1_messages, build_phase2_messages
from slices.ai_summary.retrieval_tool import TOOL_NAME, TOOL_SPEC, run_audit_context_tool
from slices.ai_summary.schemas import AiSummary
from slices.ai_summary.transformers import (
    build_error_summary,
    build_success_summary,
    parse_overview,
    parse_problematic_pages,
)
from slices.reporting.schemas import AuditReport


def _tool_handler(audit_id: str) -> ToolHandler:
    """Bind the deterministic retrieval tool to one audit's stored dataset.

    audit_id is captured here, not exposed to the model, so the LLM cannot
    point the tool at a different audit.
    """

    def handler(name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name != TOOL_NAME:
            return {"error": f"Unknown tool {name!r}."}
        return run_audit_context_tool(
            audit_id, mode=args.get("mode", ""), url=args.get("url")
        )

    return handler


async def generate_ai_summary(
    http_client: httpx.AsyncClient, report: AuditReport, audit_id: str
) -> AiSummary:
    """Build the curated dataset, store it, and run the two-phase LLM summary.

    Raises AiSummaryError on failure — call sites should use
    safe_generate_ai_summary so AI problems never break the audit.
    """
    logger.info(
        "function=generate_ai_summary | audit_id=%s root_url=%s",
        audit_id,
        report.root_url,
    )

    dataset = build_ai_dataset(report, audit_id)
    storage.write_dataset(dataset)

    tool_handler = _tool_handler(audit_id)
    tools = [TOOL_SPEC]

    # Completion 1 — overall website summary.
    overview_payload = await run_completion(
        http_client, build_phase1_messages(), tools, tool_handler
    )
    overview = parse_overview(overview_payload)

    # Completion 2 — per-page analysis of the weakest pages (skipped if none).
    problematic_urls = [page.url for page in dataset.general_info.problematic_pages]
    if problematic_urls:
        pages_payload = await run_completion(
            http_client, build_phase2_messages(problematic_urls), tools, tool_handler
        )
        pages = parse_problematic_pages(pages_payload)
    else:
        pages = []

    logger.info(
        "function=generate_ai_summary | result=audit_id=%s status=ok pages=%s",
        audit_id,
        len(pages),
    )
    return build_success_summary(audit_id, overview, pages)


async def safe_generate_ai_summary(
    http_client: httpx.AsyncClient, report: AuditReport, audit_id: str
) -> AiSummary:
    """Non-critical wrapper — AI failures never break the audit.

    Returns an AiSummary with status=error (and an explicit message) on any
    failure instead of raising.
    """
    try:
        return await generate_ai_summary(http_client, report, audit_id)
    except AiSummaryError as exc:
        logger.warning(
            "function=safe_generate_ai_summary | audit_id=%s status=error code=%s message=%s",
            audit_id,
            exc.code,
            exc.message,
        )
        return build_error_summary(audit_id, exc.message)
    except Exception as exc:  # noqa: BLE001 - AI must never crash the audit
        logger.exception(
            "function=safe_generate_ai_summary | audit_id=%s status=error unexpected",
            audit_id,
        )
        return build_error_summary(audit_id, f"Unexpected AI summary error: {exc}")
