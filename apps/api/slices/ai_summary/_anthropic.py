from __future__ import annotations

import json
from typing import Any

import httpx

from core.config import settings
from core.exceptions import AiSummaryError
from core.logging import logger
from slices.ai_summary._common import (
    ToolHandler,
    parse_json_content,
    raise_for_auth_or_client_error,
)

ANTHROPIC_VERSION = "2023-06-01"


async def run_completion(
    client: httpx.AsyncClient,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_handler: ToolHandler,
    *,
    base_url: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """Run one logical completion against /v1/messages, resolving tool calls."""
    system_text, working = _split_system(messages)
    anthropic_tools = [_translate_tool(tool) for tool in tools]

    has_tool_result = False
    for iteration in range(settings.ai_summary_max_tool_iterations + 1):
        tool_choice = {"type": "none"} if has_tool_result else {"type": "auto"}
        message = await _post_messages(
            client,
            system_text,
            working,
            anthropic_tools,
            tool_choice=tool_choice,
            base_url=base_url,
            model=model,
            api_key=api_key,
        )
        content_blocks = message.get("content", [])
        tool_use_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]
        if not tool_use_blocks:
            return parse_json_content(_extract_text(content_blocks))

        logger.info(
            "function=run_completion | dialect=anthropic iteration=%s tool_calls=%s",
            iteration,
            len(tool_use_blocks),
        )
        working.append({"role": "assistant", "content": content_blocks})
        results: list[dict[str, Any]] = []
        for block in tool_use_blocks:
            args = block.get("input")
            result = tool_handler(
                block.get("name", ""), args if isinstance(args, dict) else {}
            )
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.get("id", ""),
                    "content": json.dumps(result),
                }
            )
        working.append({"role": "user", "content": results})
        has_tool_result = True

    raise AiSummaryError(
        f"AI tool loop exceeded {settings.ai_summary_max_tool_iterations} iterations.",
        code="AI_TOOL_LOOP_EXCEEDED",
    )


async def ping(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    model: str,
    api_key: str,
) -> None:
    """Minimal request used to validate a key. Raises on auth/other failure."""
    payload = {
        "model": model,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
    }
    try:
        response = await client.post(
            f"{base_url}/messages",
            json=payload,
            headers=_headers(api_key),
            timeout=settings.ai_summary_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise AiSummaryError(
            f"Could not reach the provider: {exc}", code="AI_REQUEST_FAILED"
        ) from exc
    raise_for_auth_or_client_error(response)


async def _post_messages(
    client: httpx.AsyncClient,
    system_text: str | None,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    *,
    tool_choice: dict[str, Any],
    base_url: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """One POST to /v1/messages. Retries once on transient failures."""
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": settings.ai_summary_max_tokens,
        "messages": messages,
        "tools": tools,
        "tool_choice": tool_choice,
        "temperature": 0.2,
    }
    if system_text:
        payload["system"] = system_text
    url = f"{base_url}/messages"

    last_error = "unknown error"
    for attempt in range(2):
        try:
            response = await client.post(
                url,
                json=payload,
                headers=_headers(api_key),
                timeout=settings.ai_summary_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            last_error = f"transport error: {exc}"
            logger.warning("function=_post_messages | attempt=%s %s", attempt, last_error)
            continue

        status = response.status_code
        if status in (401, 403):
            raise AiSummaryError(
                f"The provider rejected the API key (HTTP {status}).",
                code="AI_AUTH_FAILED",
            )
        if 400 <= status < 500 and status != 429:
            raise AiSummaryError(
                f"The provider request failed (HTTP {status}).",
                code="AI_REQUEST_FAILED",
            )
        if status == 429 or status >= 500:
            last_error = f"HTTP {status}"
            logger.warning(
                "function=_post_messages | attempt=%s upstream %s", attempt, last_error
            )
            continue

        try:
            body = response.json()
        except ValueError as exc:
            last_error = f"malformed response: {exc}"
            logger.warning("function=_post_messages | attempt=%s %s", attempt, last_error)
            continue
        if body.get("stop_reason") == "max_tokens":
            logger.warning(
                "function=_post_messages | stop_reason=max_tokens — response may be truncated"
            )
        return body

    raise AiSummaryError(
        f"Provider call failed after retry ({last_error}).",
        code="AI_REQUEST_FAILED",
    )


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "Content-Type": "application/json",
    }


def _split_system(
    messages: list[dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Pull the system message out to Anthropic's top-level `system` field."""
    system_text: str | None = None
    rest: list[dict[str, Any]] = []
    for message in messages:
        if message.get("role") == "system":
            content = message.get("content")
            system_text = content if isinstance(content, str) else system_text
        else:
            rest.append(dict(message))
    return system_text, rest


def _translate_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """OpenAI function-tool spec -> Anthropic tool spec."""
    function = tool.get("function", {})
    return {
        "name": function.get("name", ""),
        "description": function.get("description", ""),
        "input_schema": function.get("parameters", {"type": "object", "properties": {}}),
    }


def _extract_text(content_blocks: list[dict[str, Any]]) -> str:
    return "".join(
        block.get("text", "")
        for block in content_blocks
        if block.get("type") == "text"
    )
