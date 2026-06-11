"use client";

import { useAuditFlow } from "@/hooks/useAuditFlow";
import { useI18n } from "@/lib/i18n";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { IdlePlaceholder } from "@/components/ui/IdlePlaceholder";
import { ErrorView } from "@/components/ui/ErrorView";
import { DiscoverForm } from "@/components/discovery/DiscoverForm";
import { DiscoveryLog } from "@/components/discovery/DiscoveryLog";
import { UrlSelectionView } from "@/components/discovery/UrlSelectionView";
import { ReportView } from "@/components/audit/ReportView";

export default function Home() {
  const {
    appState,
    discovery,
    selectedUrls,
    selectedChecks,
    report,
    errorMsg,
    progressMessages,
    discoveryElapsed,
    discoveryMaxDuration,
    auditProgressMessages,
    auditElapsed,
    auditMaxDuration,
    handleDiscover,
    handleAudit,
    handleReset,
    toggleUrl,
    toggleAllUrls,
    toggleCheck,
  } = useAuditFlow();
  const { dict } = useI18n();

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-accent/30 selection:text-accent">
      <Header />

      <main className="mx-auto max-w-7xl px-6 py-12 md:px-8 md:py-16">
        <section className="max-w-3xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/40 px-3 py-1">
            <span className="size-1.5 animate-pulse rounded-full bg-accent" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-accent">
              {dict.home.engineOnline}
            </span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            {dict.home.heroTitle}
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
            {dict.home.heroSubtitle}
          </p>

          {(appState === "idle" || appState === "error") && (
            <DiscoverForm onSubmit={handleDiscover} />
          )}
        </section>

        {appState === "idle" && <IdlePlaceholder />}
        {appState === "discovering" && (
          <DiscoveryLog
            messages={progressMessages}
            elapsedSeconds={discoveryElapsed}
            maxDurationSeconds={discoveryMaxDuration}
          />
        )}
        {appState === "selecting" && discovery && (
          <UrlSelectionView
            discovery={discovery}
            selectedUrls={selectedUrls}
            selectedChecks={selectedChecks}
            onToggle={toggleUrl}
            onToggleAll={toggleAllUrls}
            onToggleCheck={toggleCheck}
            onAudit={handleAudit}
            onReset={handleReset}
          />
        )}
        {appState === "auditing" && (
          <DiscoveryLog
            messages={auditProgressMessages}
            elapsedSeconds={auditElapsed}
            maxDurationSeconds={auditMaxDuration}
          />
        )}
        {appState === "done" && report && <ReportView report={report} />}
        {appState === "error" && (
          <ErrorView message={errorMsg ?? dict.common.unexpectedError} onReset={handleReset} />
        )}
      </main>

      <Footer />
    </div>
  );
}
