from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import ServiceMonitorError, service_monitor_exception_handler
from slices.audit.router import router as audit_router
from slices.discovery.router import router as discovery_router
from slices.health_check.router import router as health_check_router
from slices.input_validation.router import router as input_validation_router
from slices.reporting.router import router as reporting_router
from slices.seo.router import router as seo_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        description="Deterministic website auditing platform",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(ServiceMonitorError, service_monitor_exception_handler)

    app.include_router(input_validation_router, prefix="/api/v1")
    app.include_router(discovery_router, prefix="/api/v1")
    app.include_router(health_check_router, prefix="/api/v1")
    app.include_router(seo_router, prefix="/api/v1")
    app.include_router(reporting_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")

    return app


app = create_app()
