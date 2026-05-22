from __future__ import annotations

import re
from pathlib import Path

from core.config import settings
from core.exceptions import AiSummaryError
from core.logging import logger
from slices.ai_summary.schemas import AiAnalysisDataset

# audit_id is always uuid4().hex — 32 lowercase hex chars. Validated before it
# ever touches the filesystem to rule out path traversal.
_AUDIT_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def _storage_dir() -> Path:
    if settings.ai_storage_dir:
        return Path(settings.ai_storage_dir)
    # apps/api/slices/ai_summary/storage.py -> parents[2] == apps/api
    return Path(__file__).resolve().parents[2] / "storage" / "ai_context"


def _validate_audit_id(audit_id: str) -> str:
    if not _AUDIT_ID_RE.match(audit_id):
        raise AiSummaryError(
            f"Invalid audit_id for AI dataset storage: {audit_id!r}",
            code="AI_INVALID_AUDIT_ID",
        )
    return audit_id


def dataset_path(audit_id: str) -> Path:
    return _storage_dir() / f"{_validate_audit_id(audit_id)}.json"


def write_dataset(dataset: AiAnalysisDataset) -> Path:
    """Persist the curated dataset, overwriting any previous file for this audit."""
    path = dataset_path(dataset.audit_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")
    logger.info(
        "function=write_dataset | audit_id=%s path=%s", dataset.audit_id, path
    )
    return path


def read_dataset(audit_id: str) -> AiAnalysisDataset:
    path = dataset_path(audit_id)
    if not path.exists():
        raise AiSummaryError(
            f"AI dataset not found for audit {audit_id}",
            code="AI_DATASET_NOT_FOUND",
        )
    try:
        return AiAnalysisDataset.model_validate_json(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise AiSummaryError(
            f"AI dataset for audit {audit_id} is unreadable: {exc}",
            code="AI_DATASET_CORRUPT",
        ) from exc
