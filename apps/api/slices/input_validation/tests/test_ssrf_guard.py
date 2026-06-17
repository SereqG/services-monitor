from __future__ import annotations

import ipaddress

import pytest

from core.exceptions import SSRFAttemptError
from core.ssrf import assert_host_allowed, is_blocked_ip


@pytest.mark.parametrize(
    "address,reason",
    [
        ("127.0.0.1", "SSRF_LOOPBACK"),
        ("169.254.169.254", "SSRF_LINK_LOCAL"),  # cloud metadata
        ("10.0.0.5", "SSRF_PRIVATE_IP"),
        ("192.168.1.1", "SSRF_PRIVATE_IP"),
        ("100.64.0.1", "SSRF_CGNAT"),
        ("0.0.0.0", "SSRF_PRIVATE_IP"),  # 0.0.0.0/8 is classified private by ipaddress
        ("::1", "SSRF_LOOPBACK"),
        ("fe80::1", "SSRF_LINK_LOCAL"),
        ("::ffff:127.0.0.1", "SSRF_LOOPBACK"),  # IPv4-mapped IPv6 is unwrapped
    ],
)
def test_blocks_non_public_addresses(address: str, reason: str):
    assert is_blocked_ip(ipaddress.ip_address(address)) == reason


@pytest.mark.parametrize("address", ["8.8.8.8", "1.1.1.1", "93.184.216.34"])
def test_allows_public_addresses(address: str):
    assert is_blocked_ip(ipaddress.ip_address(address)) is None


async def test_assert_host_allowed_blocks_literal_metadata_ip():
    with pytest.raises(SSRFAttemptError) as exc:
        await assert_host_allowed("169.254.169.254")
    assert exc.value.code == "SSRF_LINK_LOCAL"


async def test_assert_host_allowed_blocks_resolved_private_ip(monkeypatch):
    # A public-looking hostname that resolves to a private address must be rejected.
    def fake_resolve(host: str):
        return [(2, "10.1.2.3")]

    monkeypatch.setattr("core.ssrf._resolve", fake_resolve)
    with pytest.raises(SSRFAttemptError) as exc:
        await assert_host_allowed("internal.example.com")
    assert exc.value.code == "SSRF_PRIVATE_IP"


async def test_assert_host_allowed_permits_resolved_public_ip(monkeypatch):
    def fake_resolve(host: str):
        return [(2, "93.184.216.34")]

    monkeypatch.setattr("core.ssrf._resolve", fake_resolve)
    await assert_host_allowed("example.com")  # no exception
