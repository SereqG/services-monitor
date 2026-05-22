from __future__ import annotations

import pytest

from core.config import settings
from core.exceptions import AiSummaryError
from slices.ai_summary.schemas import AiAnalysisDataset, GeneralInfo
from slices.ai_summary.storage import dataset_path, read_dataset, write_dataset


def _dataset(audit_id: str, root_url: str = "https://example.com/") -> AiAnalysisDataset:
    return AiAnalysisDataset(
        audit_id=audit_id,
        root_url=root_url,
        generated_at="2026-05-21T10:00:00+00:00",
        general_info=GeneralInfo(overall_score=72, grade="C"),
    )


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ai_storage_dir", str(tmp_path))


def test_write_read_roundtrip():
    dataset = _dataset("a" * 32)
    write_dataset(dataset)
    assert read_dataset("a" * 32).model_dump() == dataset.model_dump()


def test_write_overwrites_previous_dataset():
    write_dataset(_dataset("a" * 32, root_url="https://old.example.com/"))
    write_dataset(_dataset("a" * 32, root_url="https://new.example.com/"))
    assert read_dataset("a" * 32).root_url == "https://new.example.com/"


def test_read_missing_dataset_raises():
    with pytest.raises(AiSummaryError):
        read_dataset("f" * 32)


def test_read_corrupt_dataset_raises():
    path = dataset_path("a" * 32)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(AiSummaryError):
        read_dataset("a" * 32)


def test_invalid_audit_id_is_rejected():
    with pytest.raises(AiSummaryError):
        dataset_path("../../../etc/passwd")
    with pytest.raises(AiSummaryError):
        dataset_path("NOT-HEX")
    with pytest.raises(AiSummaryError):
        dataset_path("abc")  # too short
