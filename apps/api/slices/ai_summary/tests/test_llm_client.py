from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from core.config import settings
from core.exceptions import AiSummaryError
from slices.ai_summary.llm_client import run_completion
from slices.ai_summary.retrieval_tool import TOOL_SPEC


def _final(content: str) -> dict[str, Any]:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


def _tool_call(call_id: str, name: str, arguments: str) -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": name, "arguments": arguments},
                        }
                    ],
                }
            }
        ]
    }


class _Script:
    """Scripted httpx transport: each request pops the next step.

    A step is either (status_code, json_body) or an Exception to raise.
    """

    def __init__(self, steps: list[Any]) -> None:
        self._steps = list(steps)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        step = self._steps.pop(0)
        if isinstance(step, Exception):
            raise step
        status, body = step
        if body is None:
            return httpx.Response(status_code=status)
        return httpx.Response(status_code=status, json=body)


def _client(script: _Script) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(script))


def _handler(_name: str, _args: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True}


_MESSAGES = [{"role": "user", "content": "summarize"}]


async def test_single_turn_returns_parsed_json(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    script = _Script([(200, _final('{"overall_assessment": "Looks good"}'))])
    async with _client(script) as client:
        result = await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)
    assert result["overall_assessment"] == "Looks good"
    assert len(script.requests) == 1


async def test_tool_call_loop_appends_tool_result(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    script = _Script(
        [
            (200, _tool_call("call_1", "audit_context_tool", '{"mode": "general_info"}')),
            (200, _final('{"overall_assessment": "Done"}')),
        ]
    )
    calls: list[tuple[str, dict[str, Any]]] = []

    def handler(name: str, args: dict[str, Any]) -> dict[str, Any]:
        calls.append((name, args))
        return {"overall_score": 70}

    async with _client(script) as client:
        result = await run_completion(client, _MESSAGES, [TOOL_SPEC], handler)

    assert result["overall_assessment"] == "Done"
    assert calls == [("audit_context_tool", {"mode": "general_info"})]
    second_body = json.loads(script.requests[1].content)
    tool_messages = [m for m in second_body["messages"] if m.get("role") == "tool"]
    assert tool_messages and tool_messages[0]["tool_call_id"] == "call_1"
    assert second_body["tool_choice"] == "none"
    assert second_body.get("response_format") == {"type": "json_object"}


async def test_retries_once_on_http_429(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    script = _Script([(429, None), (200, _final('{"overall_assessment": "OK"}'))])
    async with _client(script) as client:
        result = await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)
    assert result["overall_assessment"] == "OK"
    assert len(script.requests) == 2


async def test_retries_once_on_transport_error(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    script = _Script(
        [httpx.ConnectError("boom"), (200, _final('{"overall_assessment": "OK"}'))]
    )
    async with _client(script) as client:
        result = await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)
    assert result["overall_assessment"] == "OK"


async def test_gives_up_after_retry_on_http_500(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    script = _Script([(500, None), (500, None)])
    async with _client(script) as client:
        with pytest.raises(AiSummaryError):
            await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)
    assert len(script.requests) == 2


async def test_auth_failure_is_terminal_without_retry(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "bad-key")
    script = _Script([(401, None)])
    async with _client(script) as client:
        with pytest.raises(AiSummaryError):
            await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)
    assert len(script.requests) == 1


async def test_first_request_uses_auto_tool_choice(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    script = _Script([(200, _final('{"overall_assessment": "Done"}'))])
    async with _client(script) as client:
        await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)
    first_body = json.loads(script.requests[0].content)
    assert first_body["tool_choice"] == "auto"
    assert "response_format" not in first_body


async def test_tool_loop_exceeded_raises(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, "ai_summary_max_tool_iterations", 1)
    tool_step = (200, _tool_call("c", "audit_context_tool", '{"mode": "general_info"}'))
    script = _Script([tool_step, tool_step])
    async with _client(script) as client:
        with pytest.raises(AiSummaryError):
            await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)


async def test_malformed_json_content_raises(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    script = _Script([(200, _final("this is not json"))])
    async with _client(script) as client:
        with pytest.raises(AiSummaryError):
            await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)


async def test_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    script = _Script([])
    async with _client(script) as client:
        with pytest.raises(AiSummaryError):
            await run_completion(client, _MESSAGES, [TOOL_SPEC], _handler)
