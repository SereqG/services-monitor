from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from core.config import settings
from core.exceptions import AiSummaryError
from core.logging import logger

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# (tool_name, arguments) -> tool result. Bound to a single audit by the caller.
ToolHandler = Callable[[str, dict[str, Any]], dict[str, Any]]


async def run_completion(
    client: httpx.AsyncClient,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_handler: ToolHandler,
) -> dict[str, Any]:
    """Run one logical OpenRouter completion, resolving any tool calls.

    Returns the parsed JSON object from the model's final (non-tool) message.
    Raises AiSummaryError on any failure — the caller decides how to degrade.
    """
    if not settings.openrouter_api_key:
        raise AiSummaryError(
            "OpenRouter API key is not configured.", code="AI_NO_API_KEY"
        )

    working: list[dict[str, Any]] = list(messages)
    has_tool_result = False
    for iteration in range(settings.ai_summary_max_tool_iterations + 1):
        tool_choice = "none" if has_tool_result else "auto"
        message = await _post_chat(client, working, tools, tool_choice=tool_choice)
        working.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return _parse_json_content(message.get("content"))

        logger.info(
            "function=run_completion | iteration=%s tool_calls=%s",
            iteration,
            len(tool_calls),
        )
        for call in tool_calls:
            working.append(_handle_tool_call(call, tool_handler))
        has_tool_result = True

    raise AiSummaryError(
        f"AI tool loop exceeded {settings.ai_summary_max_tool_iterations} iterations.",
        code="AI_TOOL_LOOP_EXCEEDED",
    )


async def _post_chat(
    client: httpx.AsyncClient,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_choice: str = "auto",
) -> dict[str, Any]:
    """One POST to OpenRouter. Retries once on transient failures.

    Auth (401/403) and other 4xx errors are terminal — they will not self-heal.
    """
    payload: dict[str, Any] = {
        "model": settings.ai_summary_model,
        "messages": messages,
        "tools": tools,
        "tool_choice": tool_choice,
        "temperature": 0.2,
        "max_tokens": settings.ai_summary_max_tokens,
    }
    if tool_choice == "none":
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    last_error = "unknown error"
    for attempt in range(2):
        try:
            response = await client.post(
                OPENROUTER_URL,
                json=payload,
                headers=headers,
                timeout=settings.ai_summary_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            last_error = f"transport error: {exc}"
            logger.warning("function=_post_chat | attempt=%s %s", attempt, last_error)
            continue

        status = response.status_code
        if status in (401, 403):
            raise AiSummaryError(
                f"OpenRouter rejected the API key (HTTP {status}).",
                code="AI_AUTH_FAILED",
            )
        if 400 <= status < 500 and status != 429:
            raise AiSummaryError(
                f"OpenRouter request failed (HTTP {status}).",
                code="AI_REQUEST_FAILED",
            )
        if status == 429 or status >= 500:
            last_error = f"HTTP {status}"
            logger.warning(
                "function=_post_chat | attempt=%s upstream %s", attempt, last_error
            )
            continue

        try:
            choice = response.json()["choices"][0]
            finish_reason = choice.get("finish_reason")
            if finish_reason and finish_reason != "stop":
                logger.warning(
                    "function=_post_chat | finish_reason=%s — response may be truncated",
                    finish_reason,
                )
            return choice["message"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            last_error = f"malformed response envelope: {exc}"
            logger.warning("function=_post_chat | attempt=%s %s", attempt, last_error)
            continue

    raise AiSummaryError(
        f"OpenRouter call failed after retry ({last_error}).",
        code="AI_REQUEST_FAILED",
    )


def _handle_tool_call(call: dict[str, Any], tool_handler: ToolHandler) -> dict[str, Any]:
    function = call.get("function", {})
    name = function.get("name", "")
    try:
        args = json.loads(function.get("arguments") or "{}")
    except json.JSONDecodeError:
        args = {}
    result = tool_handler(name, args if isinstance(args, dict) else {})
    return {
        "role": "tool",
        "tool_call_id": call.get("id", ""),
        "content": json.dumps(result),
    }


def _parse_json_content(content: Any) -> dict[str, Any]:
    if not isinstance(content, str) or not content.strip():
        raise AiSummaryError(
            "AI returned an empty response.", code="AI_EMPTY_RESPONSE"
        )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AiSummaryError(
            f"AI response was not valid JSON: {exc}", code="AI_BAD_JSON"
        ) from exc
    if not isinstance(parsed, dict):
        raise AiSummaryError(
            "AI response JSON was not an object.", code="AI_BAD_JSON"
        )
    return parsed
