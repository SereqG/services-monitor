from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, field_validator

from core.config import settings


class DiscoveryRequest(BaseModel):
    url: str
    max_sites: int | None = None
    max_depth: int | None = None

    @field_validator("max_sites")
    @classmethod
    def cap_max_sites(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 1:
            raise ValueError("max_sites must be at least 1")
        return min(v, settings.discovery_max_urls)

    @field_validator("max_depth")
    @classmethod
    def cap_max_depth(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 0:
            raise ValueError("max_depth must be 0 or greater")
        return min(v, settings.discovery_max_depth)


class UrlStatus(str, Enum):
    allowed = "allowed"
    blocked_by_robots = "blocked_by_robots"
    fetch_error = "fetch_error"


class DiscoveredUrl(BaseModel):
    url: str
    depth: int
    status: UrlStatus


class RobotsPolicy(BaseModel):
    fetched: bool
    allows_root: bool
    blocked_paths: list[str]
    sitemap_urls: list[str]
    raw: str | None = None


class DiscoveryResult(BaseModel):
    root_url: str
    robots_policy: RobotsPolicy
    discovered_urls: list[DiscoveredUrl]
    total_discovered: int
    total_allowed: int
    hit_limit: bool
    duration_seconds: float


class DiscoveryEventType(str, Enum):
    phase = "phase"
    url = "url"
    complete = "complete"


class DiscoveryEvent(BaseModel):
    type: DiscoveryEventType
    message: str
    count: int | None = None
    elapsed_seconds: float | None = None
    max_duration_seconds: int | None = None
    result: DiscoveryResult | None = None
