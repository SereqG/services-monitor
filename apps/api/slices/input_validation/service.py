from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from core.exceptions import InputValidationError, SSRFAttemptError
from core.logging import logger
from core.ssrf import is_blocked_ip

MAX_URL_LENGTH = 200


def validate_url(url: str) -> str:
    """Validates URL for format, HTTPS, length, and SSRF risks."""
    logger.info("function=validate_url | url=%s", url)
    if len(url) > MAX_URL_LENGTH:
        logger.info("function=validate_url | result=invalid error=URL_TOO_LONG url=%s", url)
        raise InputValidationError(
            f"URL must not exceed {MAX_URL_LENGTH} characters", code="URL_TOO_LONG"
        )

    if not url.startswith("https://"):
        logger.info("function=validate_url | result=invalid error=INVALID_SCHEME url=%s", url)
        raise InputValidationError("URL must use HTTPS scheme", code="INVALID_SCHEME")

    parsed = urlparse(url)

    if not parsed.netloc:
        logger.info("function=validate_url | result=invalid error=INVALID_URL url=%s", url)
        raise InputValidationError("URL must include a valid domain", code="INVALID_URL")

    if parsed.path not in ("", "/"):
        logger.info("function=validate_url | result=invalid error=SUBPAGE_NOT_ALLOWED url=%s", url)
        raise InputValidationError(
            "Only root URLs are supported — no subpages as entry point",
            code="SUBPAGE_NOT_ALLOWED",
        )

    _check_ssrf(parsed.netloc)

    logger.info("function=validate_url | result=valid url=%s", url)
    return url


def _check_ssrf(host: str) -> None:
    """Blocks localhost and non-public IP literals at submission time.

    This is the fast, synchronous pre-check on the literal hostname. DNS
    resolution and redirect-hop validation happen later at fetch time via
    ``core.ssrf.assert_host_allowed`` (defence in depth).
    """
    logger.info("function=_check_ssrf | host=%s", host)
    hostname = host.split(":")[0].lower()

    if hostname in ("localhost", "127.0.0.1", "::1"):
        logger.info("function=_check_ssrf | result=blocked reason=SSRF_LOCALHOST hostname=%s", hostname)
        raise SSRFAttemptError("Access to localhost is not allowed", code="SSRF_LOCALHOST")

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        logger.info("function=_check_ssrf | result=allowed hostname=%s", hostname)
        return  # domain name, not an IP — resolved-IP safety is enforced at fetch time

    if is_blocked_ip(ip) is not None:
        logger.info(
            "function=_check_ssrf | result=blocked reason=SSRF_PRIVATE_IP hostname=%s",
            hostname,
        )
        raise SSRFAttemptError(
            "Access to private IP ranges is not allowed", code="SSRF_PRIVATE_IP"
        )

    logger.info("function=_check_ssrf | result=allowed hostname=%s", hostname)
