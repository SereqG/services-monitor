from __future__ import annotations

from typing import Any

import httpx

from slices.ai_summary import _anthropic, _openai_compat
from slices.ai_summary._common import ToolHandler
from slices.ai_summary.providers import LLMCredentials

__all__ = ["ToolHandler", "run_completion", "validate_credentials"]


async def run_completion(
    client: httpx.AsyncClient,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_handler: ToolHandler,
    *,
    credentials: LLMCredentials,
) -> dict[str, Any]:
    """Run one logical completion against the user's chosen provider.

    Dispatches on the provider's wire dialect. `messages`/`tools` are in the
    canonical OpenAI shape; the Anthropic adapter translates internally.
    """
    config = credentials.config
    adapter = _anthropic if config.family == "anthropic" else _openai_compat
    return await adapter.run_completion(
        client,
        messages,
        tools,
        tool_handler,
        base_url=config.base_url,
        model=config.model,
        api_key=credentials.api_key,
    )


async def validate_credentials(
    client: httpx.AsyncClient,
    credentials: LLMCredentials,
) -> None:
    """Make a tiny live call to verify the key works. Raises AiSummaryError."""
    config = credentials.config
    adapter = _anthropic if config.family == "anthropic" else _openai_compat
    await adapter.ping(
        client,
        base_url=config.base_url,
        model=config.model,
        api_key=credentials.api_key,
    )
