from __future__ import annotations

import ipaddress
import socket

import anyio

from core.exceptions import SSRFAttemptError
from core.logging import logger

IpAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

# Carrier-grade NAT (RFC 6598) is not flagged by ipaddress.is_private, so we
# check it explicitly. Everything else is covered by the stdlib properties below.
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")


def is_blocked_ip(ip: IpAddress) -> str | None:
    """Classify an IP for SSRF safety.

    Returns a reason code if the address must not be fetched, otherwise None.
    Uses explicit ``ipaddress`` properties so the policy is auditable: loopback,
    private (RFC 1918 / ULA), link-local (covers cloud metadata 169.254.169.254
    and IPv6 fe80::/10), reserved, multicast, and the unspecified address.
    """
    # An IPv4 address tunnelled inside IPv6 (e.g. ::ffff:127.0.0.1) must be
    # judged on its real IPv4 value, not the wrapper.
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped

    if ip.is_loopback:
        return "SSRF_LOOPBACK"
    if ip.is_link_local:
        return "SSRF_LINK_LOCAL"
    if ip.is_private:
        return "SSRF_PRIVATE_IP"
    if ip.version == 4 and ip in _CGNAT_NETWORK:
        return "SSRF_CGNAT"
    if ip.is_reserved:
        return "SSRF_RESERVED"
    if ip.is_multicast:
        return "SSRF_MULTICAST"
    if ip.is_unspecified:
        return "SSRF_UNSPECIFIED"
    return None


async def assert_host_allowed(host: str) -> None:
    """Resolve ``host`` and reject if any address it maps to is blocked.

    Applied at HTTP fetch time (including every redirect hop) as defence in
    depth against DNS-based SSRF: a public-looking hostname that resolves to an
    internal address is rejected here even though the literal string passed the
    submission-time validation.

    Note: a small TOCTOU window remains between this resolution and httpx's own
    connect (DNS rebinding). Fully closing it would require pinning the resolved
    IP into the connection; that is intentionally out of scope for this pass.
    """
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        reason = is_blocked_ip(literal)
        if reason is not None:
            logger.info(
                "function=assert_host_allowed | result=blocked host=%s reason=%s",
                host,
                reason,
            )
            raise SSRFAttemptError(
                "Access to non-public addresses is not allowed", code=reason
            )
        return

    try:
        infos = await anyio.to_thread.run_sync(_resolve, host)
    except socket.gaierror as exc:
        logger.info("function=assert_host_allowed | result=unresolved host=%s", host)
        raise SSRFAttemptError(
            "Target hostname could not be resolved", code="SSRF_DNS_FAILED"
        ) from exc

    for family, address in infos:
        ip = ipaddress.ip_address(address)
        reason = is_blocked_ip(ip)
        if reason is not None:
            logger.info(
                "function=assert_host_allowed | result=blocked host=%s ip=%s reason=%s",
                host,
                address,
                reason,
            )
            raise SSRFAttemptError(
                "Target resolves to a non-public address", code=reason
            )


def _resolve(host: str) -> list[tuple[int, str]]:
    """Return (family, ip) for every A/AAAA record of ``host``."""
    results = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    return [(family, sockaddr[0]) for family, _, _, _, sockaddr in results]
