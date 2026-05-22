"use client";

import { useState, useEffect, useRef } from "react";
import { validateAuditInput, streamDiscovery, streamAudit } from "@/lib/api";
import type { AuditReport, AuditCheckType, DiscoveryResult } from "@/lib/types/api";
import { ALL_AUDIT_CHECKS } from "@/lib/types/api";
import type { DiscoverFormValues } from "@/lib/schemas/discoverForm";

export type AppState = "idle" | "discovering" | "selecting" | "auditing" | "done" | "error";

function useClientTimer(active: boolean): number | null {
  const [elapsed, setElapsed] = useState<number | null>(null);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) {
      startRef.current = null;
      setElapsed(null);
      return;
    }
    startRef.current = Date.now();
    setElapsed(0);
    const id = setInterval(() => {
      setElapsed((Date.now() - startRef.current!) / 1000);
    }, 100);
    return () => clearInterval(id);
  }, [active]);

  return elapsed;
}

export function useAuditFlow() {
  const [formValues, setFormValues] = useState<DiscoverFormValues>({
    url: "",
    email: "",
    enable_ai_summary: false,
  });
  const [appState, setAppState] = useState<AppState>("idle");
  const [discovery, setDiscovery] = useState<DiscoveryResult | null>(null);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(new Set());
  const [selectedChecks, setSelectedChecks] = useState<Set<AuditCheckType>>(
    new Set(ALL_AUDIT_CHECKS)
  );
  const [report, setReport] = useState<AuditReport | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [discoveryMaxDuration, setDiscoveryMaxDuration] = useState<number | null>(null);
  const [auditProgressMessages, setAuditProgressMessages] = useState<string[]>([]);
  const [auditMaxDuration, setAuditMaxDuration] = useState<number | null>(null);

  const discoveryElapsed = useClientTimer(appState === "discovering");
  const auditElapsed = useClientTimer(appState === "auditing");

  const handleDiscover = async (values: DiscoverFormValues) => {
    setFormValues(values);
    setAppState("discovering");
    setDiscovery(null);
    setReport(null);
    setErrorMsg(null);
    setProgressMessages([]);
    setDiscoveryMaxDuration(null);

    try {
      await validateAuditInput({ url: values.url, email: values.email });
      const result = await streamDiscovery(
        { url: values.url, email: values.email, max_sites: values.max_sites, max_depth: values.max_depth },
        (event) => {
          setProgressMessages((prev) => [...prev, event.message]);
          console.log("Discovery event:", event);
          if (event.max_duration_seconds != null) setDiscoveryMaxDuration(event.max_duration_seconds);
        },
      );
      setDiscovery(result);
      const allowed = new Set(
        result.discovered_urls.filter((u) => u.status === "allowed").map((u) => u.url)
      );
      setSelectedUrls(allowed);
      setAppState("selecting");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "An unexpected error occurred.");
      setAppState("error");
    }
  };

  const handleAudit = async () => {
    if (!discovery) return;
    setAppState("auditing");
    setAuditProgressMessages([]);
    setAuditMaxDuration(null);

    try {
      const scope = Array.from(selectedChecks);
      const result = await streamAudit(
        {
          url: formValues.url,
          email: formValues.email,
          selected_urls: Array.from(selectedUrls),
          discovery_result: discovery,
          scope: scope.length > 0 ? scope : null,
          max_sites: formValues.max_sites,
          max_depth: formValues.max_depth,
          enable_ai_summary: formValues.enable_ai_summary,
        },
        (event) => {
          setAuditProgressMessages((prev) => [...prev, event.message]);
          if (event.max_duration_seconds != null) setAuditMaxDuration(event.max_duration_seconds);
        },
      );
      setReport(result);
      setAppState("done");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "An unexpected error occurred.");
      setAppState("error");
    }
  };

  const handleReset = () => {
    setAppState("idle");
    setDiscovery(null);
    setReport(null);
    setSelectedUrls(new Set());
    setSelectedChecks(new Set(ALL_AUDIT_CHECKS));
    setErrorMsg(null);
    setProgressMessages([]);
    setDiscoveryMaxDuration(null);
    setAuditProgressMessages([]);
    setAuditMaxDuration(null);
  };

  const toggleUrl = (u: string) => {
    setSelectedUrls((prev) => {
      const next = new Set(prev);
      if (next.has(u)) next.delete(u);
      else next.add(u);
      return next;
    });
  };

  const toggleAllUrls = () => {
    if (!discovery) return;
    const allowed = discovery.discovered_urls
      .filter((u) => u.status === "allowed")
      .map((u) => u.url);
    if (selectedUrls.size === allowed.length) {
      setSelectedUrls(new Set());
    } else {
      setSelectedUrls(new Set(allowed));
    }
  };

  const toggleCheck = (check: AuditCheckType) => {
    setSelectedChecks((prev) => {
      const next = new Set(prev);
      if (next.has(check)) next.delete(check);
      else next.add(check);
      return next;
    });
  };

  return {
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
  };
}
