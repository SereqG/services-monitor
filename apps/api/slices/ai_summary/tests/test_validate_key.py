from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from core.dependencies import get_http_client
from main import app


def _override(status: int):
    """Override the HTTP client dependency with one that always returns `status`."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=status, json={"ok": True})

    async def _dep():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            yield client
        finally:
            await client.aclose()

    return _dep


def _post(status: int, provider: str, headers: dict[str, str] | None = None):
    app.dependency_overrides[get_http_client] = _override(status)
    try:
        client = TestClient(app)
        return client.post(
            "/api/v1/ai/validate-key", json={"provider": provider}, headers=headers or {}
        )
    finally:
        app.dependency_overrides.pop(get_http_client, None)


def test_validate_key_ok():
    res = _post(200, "openai", {"X-LLM-Api-Key": "sk-test"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["model"] == "gpt-5.4-mini"


def test_validate_key_rejects_bad_key():
    res = _post(401, "anthropic", {"X-LLM-Api-Key": "bad-key"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is False
    assert data["model"] == "claude-haiku-4-5-20251001"
    assert data["error"]


def test_validate_key_requires_header():
    client = TestClient(app)
    res = client.post("/api/v1/ai/validate-key", json={"provider": "openai"})
    assert res.status_code == 400
