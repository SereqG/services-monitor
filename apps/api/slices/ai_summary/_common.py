from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from core.exceptions import AiSummaryError

# (tool_name, arguments) -> tool result. Bound to a single audit by the caller.
ToolHandler = Callable[[str, dict[str, Any]], dict[str, Any]]


def parse_json_content(content: Any) -> dict[str, Any]:
    """Parse the model's final answer into a JSON object.

    Tolerates a leading/trailing ```json fence (some providers wrap JSON even
    when asked not to). Raises AiSummaryError so the caller can degrade.
    """
    if not isinstance(content, str) or not content.strip():
        raise AiSummaryError("AI returned an empty response.", code="AI_EMPTY_RESPONSE")
    text = _strip_code_fence(content)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AiSummaryError(
            f"AI response was not valid JSON: {exc}", code="AI_BAD_JSON"
        ) from exc
    if not isinstance(parsed, dict):
        raise AiSummaryError("AI response JSON was not an object.", code="AI_BAD_JSON")
    return parsed


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    # Drop the opening fence line (``` or ```json) and the closing fence.
    body = stripped.split("\n", 1)[1] if "\n" in stripped else ""
    if body.rstrip().endswith("```"):
        body = body.rstrip()[: -3]
    return body.strip()


def raise_for_auth_or_client_error(response: httpx.Response) -> None:
    """Raise on terminal HTTP errors. Used by the lightweight validation ping.

    Auth failures (401/403) get a distinct code so the validate-key endpoint can
    show a "your key was rejected" message rather than a generic failure.
    """
    status = response.status_code
    if status in (401, 403):
        raise AiSummaryError(
            f"The provider rejected the API key (HTTP {status}).",
            code="AI_AUTH_FAILED",
        )
    if status >= 400:
        raise AiSummaryError(
            f"The provider request failed (HTTP {status}).",
            code="AI_REQUEST_FAILED",
        )
