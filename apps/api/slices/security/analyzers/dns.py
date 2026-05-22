from __future__ import annotations

import asyncio

import dns.exception
import dns.resolver

from slices.security.schemas import DnsResult, SecurityFinding, Severity


def _has_spf(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, "TXT")
        for rdata in answers:
            for txt_string in rdata.strings:
                if txt_string.decode("utf-8", errors="ignore").startswith("v=spf1"):
                    return True
    except dns.exception.DNSException:
        pass
    return False


def _has_dmarc(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        for rdata in answers:
            for txt_string in rdata.strings:
                if "v=DMARC1" in txt_string.decode("utf-8", errors="ignore"):
                    return True
    except dns.exception.DNSException:
        pass
    return False


def _has_caa(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "CAA")
        return True
    except dns.resolver.NoAnswer:
        return False
    except dns.exception.DNSException:
        return False


def _has_dnssec(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "DNSKEY")
        return True
    except dns.resolver.NoAnswer:
        return False
    except dns.exception.DNSException:
        return False


async def analyze_dns(domain: str) -> DnsResult:
    loop = asyncio.get_event_loop()
    spf, dmarc, caa, dnssec = await asyncio.gather(
        loop.run_in_executor(None, _has_spf, domain),
        loop.run_in_executor(None, _has_dmarc, domain),
        loop.run_in_executor(None, _has_caa, domain),
        loop.run_in_executor(None, _has_dnssec, domain),
    )

    findings: list[SecurityFinding] = []

    if not spf:
        findings.append(
            SecurityFinding(
                category="dns",
                title="Missing SPF record",
                description="No SPF record found. Sender Policy Framework is not enforced.",
                severity=Severity.medium,
                affected_resource=domain,
                remediation=f"Add a TXT record at {domain} with an SPF policy (e.g. 'v=spf1 include:... -all').",
            )
        )

    if not dmarc:
        findings.append(
            SecurityFinding(
                category="dns",
                title="Missing DMARC record",
                description="No DMARC policy found. Email spoofing is not mitigated.",
                severity=Severity.medium,
                affected_resource=f"_dmarc.{domain}",
                remediation=f"Add a DMARC TXT record at _dmarc.{domain} (e.g. 'v=DMARC1; p=quarantine').",
            )
        )

    if not caa:
        findings.append(
            SecurityFinding(
                category="dns",
                title="Missing CAA record",
                description="No CAA record restricts certificate issuance for this domain.",
                severity=Severity.low,
                affected_resource=domain,
                remediation="Add CAA records to specify which certificate authorities may issue certificates.",
            )
        )

    if not dnssec:
        findings.append(
            SecurityFinding(
                category="dns",
                title="DNSSEC not enabled",
                description="DNSSEC is not configured. DNS responses cannot be cryptographically verified.",
                severity=Severity.low,
                affected_resource=domain,
                remediation="Enable DNSSEC at your DNS registrar to protect against DNS spoofing.",
            )
        )

    checks_passed = sum([spf, dmarc, caa, dnssec])
    score = round(checks_passed / 4 * 100)

    return DnsResult(
        score=score,
        spf_present=spf,
        dmarc_present=dmarc,
        dnssec_enabled=dnssec,
        caa_present=caa,
        findings=findings,
    )
