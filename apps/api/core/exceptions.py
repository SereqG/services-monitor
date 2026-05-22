from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class ServiceMonitorError(Exception):
    def __init__(self, message: str, code: str) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class InputValidationError(ServiceMonitorError):
    pass


class SSRFAttemptError(ServiceMonitorError):
    pass


class CrawlError(ServiceMonitorError):
    pass


class AiSummaryError(ServiceMonitorError):
    pass


async def service_monitor_exception_handler(
    request: Request, exc: ServiceMonitorError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message},
    )
