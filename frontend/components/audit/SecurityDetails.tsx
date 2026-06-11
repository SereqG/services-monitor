"use client";

import type {
  SecurityAuditResult,
  SecurityFinding,
  Severity,
  HeadersResult,
  TlsResult,
  CookieResult,
  DnsResult,
  FrontendSecurityResult,
  DependencyResult,
  BestPracticesResult,
} from "@/lib/types/api";
import { scoreStatus, statusColor, statusBar, issueSeverityColor } from "@/lib/utils/scoring";
import { useI18n, localizeFinding } from "@/lib/i18n";

const SECURITY_HEADERS = [
  "Strict-Transport-Security",
  "Content-Security-Policy",
  "X-Frame-Options",
  "X-Content-Type-Options",
  "X-XSS-Protection",
  "Referrer-Policy",
  "Permissions-Policy",
];

function SubScore({ label, score }: { label: string; score: number }) {
  const status = scoreStatus(score);
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        {label}
      </div>
      <div className={`font-mono text-2xl font-bold ${statusColor(status)}`}>{score}</div>
      <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-secondary">
        <div className={`h-full ${statusBar(status)}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

function CheckRow({
  label,
  note,
  pass,
  value,
}: {
  label: string;
  note?: string;
  pass: boolean;
  value?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border py-3 last:border-0">
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium">{label}</span>
        {note && <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">{note}</p>}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {value && (
          <span className="max-w-[200px] truncate text-right font-mono text-xs text-muted-foreground">
            {value}
          </span>
        )}
        <span className={`font-mono text-[10px] ${pass ? "text-accent" : "text-destructive"}`}>
          {pass ? "✓" : "✗"}
        </span>
      </div>
    </div>
  );
}

function FindingRow({ finding }: { finding: SecurityFinding }) {
  const { lang, dict } = useI18n();
  const text = localizeFinding(finding, lang);
  return (
    <div className="rounded-lg border border-border bg-card/50 p-3">
      <div className="flex items-start gap-2">
        <span
          className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[9px] uppercase ${issueSeverityColor(finding.severity as Severity)}`}
        >
          {dict.severity[finding.severity] ?? finding.severity}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">{text.title}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{text.description}</p>
          {finding.evidence && (
            <p className="mt-1 font-mono text-[10px] text-muted-foreground">
              {dict.securityDetails.evidence}: {finding.evidence}
            </p>
          )}
          {text.remediation && (
            <p className="mt-1 text-xs text-accent/80">{text.remediation}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        {title}
      </h4>
      {children}
    </div>
  );
}

function HeadersSection({ headers }: { headers: HeadersResult }) {
  const { dict } = useI18n();
  const presentSet = new Set(headers.headers_present);
  return (
    <Section title={dict.securityDetails.sections.headers}>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        {SECURITY_HEADERS.map((name) => (
          <CheckRow key={name} label={name} pass={presentSet.has(name)} />
        ))}
      </div>
      {headers.findings.length > 0 && (
        <div className="mt-3 space-y-2">
          {headers.findings.map((f, i) => (
            <FindingRow key={i} finding={f} />
          ))}
        </div>
      )}
    </Section>
  );
}

function TlsSection({ tls }: { tls: TlsResult }) {
  const { dict } = useI18n();
  const t = dict.securityDetails;
  const certExpiry = tls.certificate_expiry_days;
  const certValidValue =
    tls.certificate_valid === null
      ? dict.common.unknown
      : tls.certificate_valid
      ? dict.common.valid
      : dict.common.invalid;
  return (
    <Section title={t.sections.tls}>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label={t.rows.tlsVersion.label}
          note={t.rows.tlsVersion.note}
          pass={tls.tls_version !== null && (tls.tls_version === "TLSv1.2" || tls.tls_version === "TLSv1.3")}
          value={tls.tls_version ?? dict.common.unknown}
        />
        <CheckRow
          label={t.rows.certValid.label}
          note={t.rows.certValid.note}
          pass={tls.certificate_valid === true}
          value={certValidValue}
        />
        <CheckRow
          label={t.rows.certExpiry.label}
          note={t.rows.certExpiry.note}
          pass={certExpiry !== null && certExpiry > 30}
          value={certExpiry !== null ? t.daysValue(certExpiry) : dict.common.unknown}
        />
      </div>
      {tls.findings.length > 0 && (
        <div className="mt-3 space-y-2">
          {tls.findings.map((f, i) => (
            <FindingRow key={i} finding={f} />
          ))}
        </div>
      )}
    </Section>
  );
}

function CookiesSection({ cookies }: { cookies: CookieResult }) {
  const { dict } = useI18n();
  return (
    <Section title={dict.securityDetails.sections.cookies}>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label={dict.securityDetails.rows.totalCookies.label}
          pass={cookies.total_cookies === 0 || cookies.findings.length === 0}
          value={String(cookies.total_cookies)}
        />
      </div>
      {cookies.findings.length > 0 && (
        <div className="mt-3 space-y-2">
          {cookies.findings.map((f, i) => (
            <FindingRow key={i} finding={f} />
          ))}
        </div>
      )}
    </Section>
  );
}

function DnsSection({ dns }: { dns: DnsResult }) {
  const { dict } = useI18n();
  const t = dict.securityDetails;
  return (
    <Section title={t.sections.dns}>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label={t.rows.spf.label}
          note={t.rows.spf.note}
          pass={dns.spf_present}
          value={dns.spf_present ? dict.common.present : dict.common.missing}
        />
        <CheckRow
          label={t.rows.dmarc.label}
          note={t.rows.dmarc.note}
          pass={dns.dmarc_present}
          value={dns.dmarc_present ? dict.common.present : dict.common.missing}
        />
        <CheckRow
          label={t.rows.dnssec.label}
          note={t.rows.dnssec.note}
          pass={dns.dnssec_enabled}
          value={dns.dnssec_enabled ? dict.common.enabled : dict.common.disabled}
        />
        <CheckRow
          label={t.rows.caa.label}
          note={t.rows.caa.note}
          pass={dns.caa_present}
          value={dns.caa_present ? dict.common.present : dict.common.missing}
        />
      </div>
      {dns.findings.length > 0 && (
        <div className="mt-3 space-y-2">
          {dns.findings.map((f, i) => (
            <FindingRow key={i} finding={f} />
          ))}
        </div>
      )}
    </Section>
  );
}

function FrontendSection({ frontend }: { frontend: FrontendSecurityResult }) {
  const { dict } = useI18n();
  return (
    <Section title={dict.securityDetails.sections.frontend}>
      {frontend.technologies_detected.length > 0 && (
        <div className="mb-3 overflow-hidden rounded-xl border border-border bg-card/50 px-4 py-3">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {dict.securityDetails.technologiesDetected}
          </div>
          <div className="flex flex-wrap gap-2">
            {frontend.technologies_detected.map((tech) => (
              <span
                key={tech}
                className="rounded border border-border bg-secondary px-2 py-0.5 font-mono text-xs"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}
      {frontend.findings.length > 0 ? (
        <div className="space-y-2">
          {frontend.findings.map((f, i) => (
            <FindingRow key={i} finding={f} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card/50 px-4 py-3 font-mono text-xs text-accent">
          {dict.securityDetails.noFrontendIssues}
        </div>
      )}
    </Section>
  );
}

function DependenciesSection({ dependencies }: { dependencies: DependencyResult }) {
  const { dict } = useI18n();
  return (
    <Section title={dict.securityDetails.sections.dependencies}>
      {dependencies.js_libraries.length > 0 && (
        <div className="mb-3 overflow-hidden rounded-xl border border-border bg-card/50 px-4 py-3">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {dict.securityDetails.librariesDetected}
          </div>
          <div className="flex flex-wrap gap-2">
            {dependencies.js_libraries.map((lib) => (
              <span
                key={lib}
                className="rounded border border-border bg-secondary px-2 py-0.5 font-mono text-xs"
              >
                {lib}
              </span>
            ))}
          </div>
        </div>
      )}
      {dependencies.findings.length > 0 ? (
        <div className="space-y-2">
          {dependencies.findings.map((f, i) => (
            <FindingRow key={i} finding={f} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card/50 px-4 py-3 font-mono text-xs text-accent">
          {dict.securityDetails.noDependencyIssues}
        </div>
      )}
    </Section>
  );
}

function BestPracticesSection({ bp }: { bp: BestPracticesResult }) {
  const { dict } = useI18n();
  const t = dict.securityDetails;
  return (
    <Section title={t.sections.bestPractices}>
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label={t.rows.securityTxt.label}
          note={t.rows.securityTxt.note}
          pass={bp.security_txt_present}
          value={bp.security_txt_present ? dict.common.present : dict.common.missing}
        />
        <CheckRow
          label={t.rows.robotsTxt.label}
          note={t.rows.robotsTxt.note}
          pass={bp.robots_txt_present}
          value={bp.robots_txt_present ? dict.common.present : dict.common.missing}
        />
        <CheckRow
          label={t.rows.sourceMaps.label}
          note={t.rows.sourceMaps.note}
          pass={bp.sourcemaps_found.length === 0}
          value={bp.sourcemaps_found.length === 0 ? dict.common.noneFound : t.foundValue(bp.sourcemaps_found.length)}
        />
      </div>
      {bp.findings.length > 0 && (
        <div className="mt-3 space-y-2">
          {bp.findings.map((f, i) => (
            <FindingRow key={i} finding={f} />
          ))}
        </div>
      )}
    </Section>
  );
}

export function SecurityDetails({ security }: { security: SecurityAuditResult }) {
  const { dict } = useI18n();
  const t = dict.securityDetails;
  const subScores = {
    headers: security.headers.score,
    tls: security.tls.score,
    cookies: security.cookies.score,
    dns: security.dns.score,
    frontend: security.frontend.score,
    dependencies: security.dependencies.score,
    best_practices: security.best_practices.score,
  };

  const criticalAndHighFindings = security.all_findings.filter(
    (f) => f.severity === "critical" || f.severity === "high"
  );

  return (
    <div className="space-y-8">
      {/* Subcategory score grid */}
      <div>
        <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
          {t.subScores}
        </h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {Object.entries(subScores).map(([key, score]) => (
            <SubScore key={key} label={t.subcategories[key] ?? key} score={score} />
          ))}
        </div>
      </div>

      {/* Critical/high findings summary */}
      {criticalAndHighFindings.length > 0 && (
        <div>
          <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
            {t.criticalHigh(criticalAndHighFindings.length)}
          </h3>
          <div className="space-y-2">
            {criticalAndHighFindings.map((f, i) => (
              <FindingRow key={i} finding={f} />
            ))}
          </div>
        </div>
      )}

      {/* Per-subcategory detail */}
      <HeadersSection headers={security.headers} />
      <TlsSection tls={security.tls} />
      <DnsSection dns={security.dns} />
      <CookiesSection cookies={security.cookies} />
      <FrontendSection frontend={security.frontend} />
      <DependenciesSection dependencies={security.dependencies} />
      <BestPracticesSection bp={security.best_practices} />
    </div>
  );
}
