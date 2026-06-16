from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from core.exceptions import AiSummaryError
from slices.ai_summary.llm_client import run_completion
from slices.ai_summary.providers import LLMCredentials
from slices.ai_summary.retrieval_tool import TOOL_SPEC

_CREDS = LLMCredentials(provider="anthropic", api_key="test-key")
# Mirrors the canonical (OpenAI-shaped) messages the prompt builder produces.
_MESSAGES = [
    {"role": "system", "content": "You explain audits."},
    {"role": "user", "content": "summarize"},
]


def _text(content: str) -> dict[str, Any]:
    return {"stop_reason": "end_turn", "content": [{"type": "text", "text": content}]}


def _tool_use(use_id: str, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "stop_reason": "tool_use",
        "content": [{"type": "tool_use", "id": use_id, "name": name, "input": tool_input}],
    }


class _Script:
    def __init__(self, steps: list[Any]) -> None:
        self._steps = list(steps)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        step = self._steps.pop(0)
        status, body = step
        if body is None:
            return httpx.Response(status_code=status)
        return httpx.Response(status_code=status, json=body)


def _client(script: _Script) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(script))


def _handler(_name: str, _args: dict[str, Any]) -> dict[str, Any]:
    return {"overall_score": 70}


async def test_single_turn_parses_text_block():
    script = _Script([(200, _text('{"overall_assessment": "Looks good"}'))])
    async with _client(script) as client:
        result = await run_completion(
            client, _MESSAGES, [TOOL_SPEC], _handler, credentials=_CREDS
        )
    assert result["overall_assessment"] == "Looks good"


async def test_request_translates_system_and_tools():
    script = _Script([(200, _text('{"overall_assessment": "ok"}'))])
    async with _client(script) as client:
        await run_completion(
            client, _MESSAGES, [TOOL_SPEC], _handler, credentials=_CREDS
        )
    request = script.requests[0]
    assert str(request.url) == "https://api.anthropic.com/v1/messages"
    assert request.headers["x-api-key"] == "test-key"
    assert request.headers["anthropic-version"] == "2023-06-01"
    body = json.loads(request.content)
    # System pulled out of messages into the top-level field.
    assert body["system"] == "You explain audits."
    assert all(m["role"] != "system" for m in body["messages"])
    assert body["model"] == "claude-haiku-4-5-20251001"
    # Tool spec translated to Anthropic shape (input_schema, no `function` wrapper).
    tool = body["tools"][0]
    assert tool["name"] == "audit_context_tool"
    assert "input_schema" in tool and "function" not in tool


async def test_tool_loop_translates_tool_use_and_result():
    script = _Script(
        [
            (200, _tool_use("tu_1", "audit_context_tool", {"mode": "general_info"})),
            (200, _text('{"overall_assessment": "Done"}')),
        ]
    )
    calls: list[tuple[str, dict[str, Any]]] = []

    def handler(name: str, args: dict[str, Any]) -> dict[str, Any]:
        calls.append((name, args))
        return {"overall_score": 70}

    async with _client(script) as client:
        result = await run_completion(
            client, _MESSAGES, [TOOL_SPEC], handler, credentials=_CREDS
        )

    assert result["overall_assessment"] == "Done"
    assert calls == [("audit_context_tool", {"mode": "general_info"})]
    second = json.loads(script.requests[1].content)
    # The assistant tool_use turn and the user tool_result turn are appended.
    roles = [m["role"] for m in second["messages"]]
    assert roles[-2:] == ["assistant", "user"]
    tool_result = second["messages"][-1]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert tool_result["tool_use_id"] == "tu_1"
    assert second["tool_choice"] == {"type": "none"}


async def test_strips_json_code_fence():
    fenced = "```json\n{\"overall_assessment\": \"Fenced\"}\n```"
    script = _Script([(200, _text(fenced))])
    async with _client(script) as client:
        result = await run_completion(
            client, _MESSAGES, [TOOL_SPEC], _handler, credentials=_CREDS
        )
    assert result["overall_assessment"] == "Fenced"


async def test_auth_failure_is_terminal():
    bad = LLMCredentials(provider="anthropic", api_key="bad-key")
    script = _Script([(401, None)])
    async with _client(script) as client:
        with pytest.raises(AiSummaryError) as exc_info:
            await run_completion(
                client, _MESSAGES, [TOOL_SPEC], _handler, credentials=bad
            )
    assert exc_info.value.code == "AI_AUTH_FAILED"
    assert len(script.requests) == 1
