from __future__ import annotations

from slices.ai_summary.prompt_builder import (
    SYSTEM_PROMPT,
    build_phase1_messages,
    build_phase2_messages,
)

_PL_MARKER = "natural, fluent Polish"


def _user_content(messages: list[dict]) -> str:
    return next(m["content"] for m in messages if m["role"] == "user")


def test_phase1_english_default_has_no_polish_instruction():
    messages = build_phase1_messages()
    assert _PL_MARKER not in _user_content(messages)
    assert messages[0]["content"] == SYSTEM_PROMPT


def test_phase1_polish_appends_language_instruction():
    messages = build_phase1_messages("pl")
    content = _user_content(messages)
    assert _PL_MARKER in content
    # The base instruction is preserved; the language note is appended, not replacing it.
    assert "overall_assessment" in content


def test_phase2_english_default_has_no_polish_instruction():
    messages = build_phase2_messages(["https://example.com/a"])
    assert _PL_MARKER not in _user_content(messages)


def test_phase2_polish_appends_language_instruction():
    messages = build_phase2_messages(["https://example.com/a"], "pl")
    content = _user_content(messages)
    assert _PL_MARKER in content
    assert "https://example.com/a" in content


def test_polish_instruction_keeps_json_keys_in_english():
    content = _user_content(build_phase1_messages("pl"))
    # JSON field names must stay English so the response still validates.
    assert "field names exactly as written above, in English" in content
