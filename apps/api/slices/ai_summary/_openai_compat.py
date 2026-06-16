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

# Adapter for the OpenAI Chat Completions dialect — shared by OpenAI, OpenRouter,
# and Gemini's OpenAI-compatible endpoint. The canonical message/tool shape used
# across the ai_summary slice is exactly this dialect, so no translation needed.


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
    """Run one logical completion, resolving any tool calls.

    Returns the parsed JSON object from the model's final (non-tool) message.
    Raises AiSummaryError on any failure — the caller decides how to degrade.
    """
    working: list[dict[str, Any]] = list(messages)
    has_tool_result = False
    for iteration in range(settings.ai_summary_max_tool_iterations + 1):
        tool_choice = "none" if has_tool_result else "auto"
        message = await _post_chat(
            client,
            working,
            tools,
            tool_choice=tool_choice,
            base_url=base_url,
            model=model,
            api_key=api_key,
        )
        working.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return parse_json_content(message.get("content"))

        logger.info(
            "function=run_completion | dialect=openai iteration=%s tool_calls=%s",
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
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
        "max_completion_tokens": 16,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = await client.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=settings.ai_summary_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise AiSummaryError(
            f"Could not reach the provider: {exc}", code="AI_REQUEST_FAILED"
        ) from exc
    raise_for_auth_or_client_error(response)


async def _post_chat(
    client: httpx.AsyncClient,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    *,
    tool_choice: str,
    base_url: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """One POST to the chat-completions endpoint. Retries once on transient failures.

    Auth (401/403) and other 4xx errors are terminal — they will not self-heal.
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": tool_choice,
        "temperature": 0.2,
        "max_completion_tokens": settings.ai_summary_max_tokens,
    }
    if tool_choice == "none":
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = f"{base_url}/chat/completions"

    last_error = "unknown error"
    for attempt in range(2):
        try:
            response = await client.post(
                url,
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
        f"Provider call failed after retry ({last_error}).",
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
