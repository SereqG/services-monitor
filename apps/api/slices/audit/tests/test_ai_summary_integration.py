from __future__ import annotations

import asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

from core.config import settings
from slices.ai_summary.schemas import AiSummary, AiSummaryStatus
from slices.audit.schemas import AuditEventType, AuditRequest
from slices.audit.service import run_audit, stream_audit
from slices.audit.tests.test_service import _discovery, _patches
from slices.discovery.schemas import DiscoveredUrl

_DISCOVERED = [DiscoveredUrl(url="https://example.com/", depth=0, status="allowed")]


def _audit_patches():
    return _patches(
        {
            "slices.audit.service.run_discovery": patch(
                "slices.audit.service.run_discovery",
                new=AsyncMock(return_value=_discovery(_DISCOVERED)),
            )
        }
    )


def _run(request: AuditRequest, ai_mock: AsyncMock):
    with ExitStack() as stack:
        for active in _audit_patches().values():
            stack.enter_context(active)
        stack.enter_context(
            patch("slices.audit.service.safe_generate_ai_summary", ai_mock)
        )
        return asyncio.run(run_audit(MagicMock(), request))


def test_audit_without_ai_summary_leaves_field_none():
    request = AuditRequest(url="https://example.com/", email="t@example.com")
    ai_mock = AsyncMock()
    report = _run(request, ai_mock)

    assert report.ai_summary is None
    ai_mock.assert_not_awaited()
    assert report.audit_id  # every report carries a generated id


def test_audit_with_ai_summary_attaches_successful_summary(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, "ai_summary_enabled", True)
    request = AuditRequest(
        url="https://example.com/", email="t@example.com", enable_ai_summary=True
    )
    ai_mock = AsyncMock(
        return_value=AiSummary(status=AiSummaryStatus.ok, audit_id="a" * 32)
    )
    report = _run(request, ai_mock)

    assert report.ai_summary is not None
    assert report.ai_summary.status == AiSummaryStatus.ok
    ai_mock.assert_awaited_once()


def test_audit_ai_failure_does_not_break_audit(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    request = AuditRequest(
        url="https://example.com/", email="t@example.com", enable_ai_summary=True
    )
    ai_mock = AsyncMock(
        return_value=AiSummary(
            status=AiSummaryStatus.error, audit_id="a" * 32, error="LLM unavailable"
        )
    )
    report = _run(request, ai_mock)

    # AI failed, but the deterministic audit still produced a full report.
    assert report.ai_summary.status == AiSummaryStatus.error
    assert report.score_breakdown is not None
    assert report.discovery is not None


def test_audit_ai_enabled_without_api_key_yields_error_summary(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    request = AuditRequest(
        url="https://example.com/", email="t@example.com", enable_ai_summary=True
    )
    ai_mock = AsyncMock()
    report = _run(request, ai_mock)

    assert report.ai_summary.status == AiSummaryStatus.error
    assert "not configured" in (report.ai_summary.error or "")
    ai_mock.assert_not_awaited()  # LLM never called when unconfigured
    assert report.score_breakdown is not None


def test_stream_audit_emits_ai_summary_phase_events(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    request = AuditRequest(
        url="https://example.com/", email="t@example.com", enable_ai_summary=True
    )
    ai_mock = AsyncMock(
        return_value=AiSummary(status=AiSummaryStatus.ok, audit_id="a" * 32)
    )

    async def _collect():
        events = []
        with ExitStack() as stack:
            for active in _audit_patches().values():
                stack.enter_context(active)
            stack.enter_context(
                patch("slices.audit.service.safe_generate_ai_summary", ai_mock)
            )
            async for event in stream_audit(MagicMock(), request):
                events.append(event)
        return events

    events = asyncio.run(_collect())
    messages = [e.message for e in events]
    assert any("Generating AI summary" in m for m in messages)
    assert any("AI summary ready" in m for m in messages)

    complete = [e for e in events if e.type == AuditEventType.complete]
    assert complete[0].result.ai_summary.status == AiSummaryStatus.ok
