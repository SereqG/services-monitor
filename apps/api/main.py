from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import ServiceMonitorError, service_monitor_exception_handler
from slices.ai_summary.router import router as ai_summary_router
from slices.audit.router import router as audit_router
from slices.discovery.router import router as discovery_router
from slices.health_check.router import router as health_check_router
from slices.input_validation.router import router as input_validation_router
from slices.reporting.router import router as reporting_router
from slices.seo.router import router as seo_router

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        description="Deterministic website auditing platform",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    app.add_exception_handler(ServiceMonitorError, service_monitor_exception_handler)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        """Liveness probe for container orchestration (not a target audit)."""
        return {"status": "ok"}

    app.include_router(input_validation_router, prefix="/api/v1")
    app.include_router(discovery_router, prefix="/api/v1")
    app.include_router(health_check_router, prefix="/api/v1")
    app.include_router(seo_router, prefix="/api/v1")
    app.include_router(reporting_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(ai_summary_router, prefix="/api/v1")

    return app


app = create_app()
