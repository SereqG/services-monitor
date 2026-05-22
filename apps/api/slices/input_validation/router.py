from __future__ import annotations

from fastapi import APIRouter

from core.logging import logger
from slices.input_validation import service
from slices.input_validation.schemas import AuditInput, ValidationResult

router = APIRouter(prefix="/validate", tags=["validation"])


@router.post("", response_model=ValidationResult)
async def validate_audit_input(body: AuditInput) -> ValidationResult:
    logger.info("endpoint=POST /api/v1/validate | function=validate_audit_input | url=%s", body.url)
    url = service.validate_url(body.url)
    result = ValidationResult(
        url=url,
        email=str(body.email),
        report_name=body.report_name,
        is_valid=True,
        errors=[],
    )
    logger.info(
        "endpoint=POST /api/v1/validate | function=validate_audit_input | result=is_valid=%s url=%s",
        result.is_valid, result.url,
    )
    return result
