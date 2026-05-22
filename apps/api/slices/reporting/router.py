from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])

# Report retrieval endpoints will be added when report storage is introduced (Phase 2).
# Reports are currently returned inline from the /api/v1/audit endpoint.
