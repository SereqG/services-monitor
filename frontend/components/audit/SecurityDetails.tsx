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
  return (
    <div className="rounded-lg border border-border bg-card/50 p-3">
      <div className="flex items-start gap-2">
        <span
          className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[9px] uppercase ${issueSeverityColor(finding.severity as Severity)}`}
        >
          {finding.severity}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">{finding.title}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{finding.description}</p>
          {finding.evidence && (
            <p className="mt-1 font-mono text-[10px] text-muted-foreground">
              Evidence: {finding.evidence}
            </p>
          )}
          {finding.remediation && (
            <p className="mt-1 text-xs text-accent/80">{finding.remediation}</p>
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
  const presentSet = new Set(headers.headers_present);
  return (
    <Section title="HTTP security headers">
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
  const certExpiry = tls.certificate_expiry_days;
  return (
    <Section title="TLS / HTTPS">
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label="TLS version"
          note="TLS 1.2 or higher is required; TLS 1.3 is preferred."
          pass={tls.tls_version !== null && (tls.tls_version === "TLSv1.2" || tls.tls_version === "TLSv1.3")}
          value={tls.tls_version ?? "Unknown"}
        />
        <CheckRow
          label="Certificate valid"
          note="Certificate must be issued by a trusted CA and not expired."
          pass={tls.certificate_valid === true}
          value={tls.certificate_valid === null ? "Unknown" : tls.certificate_valid ? "Valid" : "Invalid"}
        />
        <CheckRow
          label="Certificate expiry"
          note="Certificates expiring in less than 30 days should be renewed."
          pass={certExpiry !== null && certExpiry > 30}
          value={certExpiry !== null ? `${certExpiry} days` : "Unknown"}
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
  return (
    <Section title="Cookies">
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label="Total cookies"
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
  return (
    <Section title="DNS security">
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label="SPF record"
          note="Sender Policy Framework — prevents email spoofing."
          pass={dns.spf_present}
          value={dns.spf_present ? "Present" : "Missing"}
        />
        <CheckRow
          label="DMARC record"
          note="Domain-based Message Authentication — defines policy for failed SPF/DKIM."
          pass={dns.dmarc_present}
          value={dns.dmarc_present ? "Present" : "Missing"}
        />
        <CheckRow
          label="DNSSEC"
          note="DNS Security Extensions — protects against DNS spoofing."
          pass={dns.dnssec_enabled}
          value={dns.dnssec_enabled ? "Enabled" : "Disabled"}
        />
        <CheckRow
          label="CAA record"
          note="Certification Authority Authorization — restricts which CAs can issue certificates."
          pass={dns.caa_present}
          value={dns.caa_present ? "Present" : "Missing"}
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
  return (
    <Section title="Frontend security">
      {frontend.technologies_detected.length > 0 && (
        <div className="mb-3 overflow-hidden rounded-xl border border-border bg-card/50 px-4 py-3">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Technologies detected
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
          ✓ No frontend security issues found
        </div>
      )}
    </Section>
  );
}

function DependenciesSection({ dependencies }: { dependencies: DependencyResult }) {
  return (
    <Section title="JavaScript dependencies">
      {dependencies.js_libraries.length > 0 && (
        <div className="mb-3 overflow-hidden rounded-xl border border-border bg-card/50 px-4 py-3">
          <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Libraries detected
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
          ✓ No dependency issues found
        </div>
      )}
    </Section>
  );
}

function BestPracticesSection({ bp }: { bp: BestPracticesResult }) {
  return (
    <Section title="Best practices">
      <div className="overflow-hidden rounded-xl border border-border bg-card/50 px-4">
        <CheckRow
          label="security.txt"
          note="A machine-readable file for security researchers to report vulnerabilities."
          pass={bp.security_txt_present}
          value={bp.security_txt_present ? "Present" : "Missing"}
        />
        <CheckRow
          label="robots.txt"
          note="Tells crawlers which paths to avoid. Reduces accidental exposure."
          pass={bp.robots_txt_present}
          value={bp.robots_txt_present ? "Present" : "Missing"}
        />
        <CheckRow
          label="Source maps exposed"
          note="Public source maps expose original source code to anyone who looks."
          pass={bp.sourcemaps_found.length === 0}
          value={bp.sourcemaps_found.length === 0 ? "None found" : `${bp.sourcemaps_found.length} found`}
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

const SUBCATEGORY_LABELS: Record<string, string> = {
  headers: "Headers",
  tls: "TLS",
  cookies: "Cookies",
  dns: "DNS",
  frontend: "Frontend",
  dependencies: "Dependencies",
  best_practices: "Best Practices",
};

export function SecurityDetails({ security }: { security: SecurityAuditResult }) {
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
          Security subcategory scores
        </h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {Object.entries(subScores).map(([key, score]) => (
            <SubScore key={key} label={SUBCATEGORY_LABELS[key]} score={score} />
          ))}
        </div>
      </div>

      {/* Critical/high findings summary */}
      {criticalAndHighFindings.length > 0 && (
        <div>
          <h3 className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
            Critical &amp; high findings ({criticalAndHighFindings.length})
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
