from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.config import settings
from core.logging import logger
from slices.reporting.schemas import AuditReport


def _summaries_dir() -> Path:
    if settings.summaries_dir:
        return Path(settings.summaries_dir)
    # slices/summaries/storage.py -> parents[2] == apps/api
    return Path(__file__).resolve().parents[2] / "storage" / "summaries"


def _filename_from_timestamp(generated_at: str) -> str:
    dt = datetime.fromisoformat(generated_at).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H%M%SZ") + ".json"


def save_summary(report: AuditReport) -> Path | None:
    """Persist the full AuditReport to a datetime-named JSON file.

    Non-critical: logs on failure and returns None instead of raising so the
    audit result is never lost because of a storage error.
    """
    try:
        path = _summaries_dir() / _filename_from_timestamp(report.generated_at)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        logger.info(
            "function=save_summary | audit_id=%s path=%s", report.audit_id, path
        )
        return path
    except Exception as exc:
        logger.error(
            "function=save_summary | audit_id=%s error=%s", report.audit_id, exc
        )
        return None
