from __future__ import annotations

import json

import pytest

from core.config import settings
from slices.ai_summary.tests._builders import report
from slices.summaries.storage import _filename_from_timestamp, save_summary


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "summaries_dir", str(tmp_path))


def test_filename_utc_timestamp():
    assert _filename_from_timestamp("2026-05-22T10:30:45+00:00") == "2026-05-22T103045Z.json"


def test_filename_non_utc_timestamp_converted():
    # +02:00 offset — stored as UTC in the filename
    assert _filename_from_timestamp("2026-05-22T12:30:45+02:00") == "2026-05-22T103045Z.json"


def test_save_summary_writes_file(tmp_path):
    r = report(pages=[], audit_id="a" * 32)
    path = save_summary(r)

    assert path is not None
    assert path.exists()
    assert path.name == "2026-05-21T100000Z.json"


def test_save_summary_file_is_valid_json(tmp_path):
    r = report(pages=[], audit_id="b" * 32)
    path = save_summary(r)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["audit_id"] == "b" * 32
    assert data["root_url"] == "https://example.com/"


def test_save_summary_creates_parent_dir(tmp_path, monkeypatch):
    nested = tmp_path / "deep" / "nested"
    monkeypatch.setattr(settings, "summaries_dir", str(nested))

    r = report(pages=[])
    path = save_summary(r)

    assert path is not None
    assert path.exists()


def test_save_summary_returns_none_on_io_error(monkeypatch):
    monkeypatch.setattr(settings, "summaries_dir", "/proc/nonexistent_readonly_path")

    r = report(pages=[])
    result = save_summary(r)

    assert result is None
