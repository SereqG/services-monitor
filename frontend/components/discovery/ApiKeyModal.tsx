"use client";

import { useEffect, useRef, useState } from "react";
import { useI18n } from "@/lib/i18n";
import { validateLlmKey } from "@/lib/api";
import {
  LLM_PROVIDERS,
  LLM_PROVIDER_IDS,
  type LlmProvider,
} from "@/lib/llm/providers";
import type { LlmCredentials } from "@/lib/llm/useLlmKey";

type Status = "idle" | "testing" | "error" | "success";

// Rendered only while open (the parent gates with `{open && <ApiKeyModal …/>}`),
// so each open is a fresh mount and transient state initializes from props.
export function ApiKeyModal({
  onClose,
  initialProvider,
  hasExistingKey,
  onSaved,
  onRemove,
}: {
  onClose: () => void;
  initialProvider?: LlmProvider | null;
  hasExistingKey?: boolean;
  onSaved: (credentials: LlmCredentials) => void;
  onRemove: () => void;
}) {
  const { dict } = useI18n();
  const t = dict.apiKeyModal;

  const [provider, setProvider] = useState<LlmProvider>(initialProvider ?? "openai");
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");
  const closeTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (closeTimer.current) window.clearTimeout(closeTimer.current);
    };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && status !== "testing") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [status, onClose]);

  const info = LLM_PROVIDERS[provider];
  const guide = t.guides[provider];

  const handleTest = async () => {
    if (!apiKey.trim()) {
      setStatus("error");
      setMessage(t.missingKey);
      return;
    }
    setStatus("testing");
    setMessage("");
    try {
      const result = await validateLlmKey(provider, apiKey.trim());
      if (result.ok) {
        onSaved({ provider, apiKey: apiKey.trim() });
        setStatus("success");
        setMessage(t.success(result.model));
        closeTimer.current = window.setTimeout(onClose, 1200);
      } else {
        setStatus("error");
        setMessage(`${t.failurePrefix} ${result.error ?? ""}`.trim());
      }
    } catch (err) {
      setStatus("error");
      setMessage(
        `${t.failurePrefix} ${err instanceof Error ? err.message : "unexpected error"}`,
      );
    }
  };

  const testing = status === "testing";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={() => {
        if (!testing) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="api-key-modal-title"
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-border bg-card p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col gap-1">
          <h2 id="api-key-modal-title" className="text-lg font-bold">
            {t.title}
          </h2>
          <p className="text-sm text-muted-foreground">{t.subtitle}</p>
        </div>

        <div className="mt-5 flex flex-col gap-4">
          {/* Provider */}
          <label className="flex flex-col gap-1">
            <span className="px-1 text-xs text-muted-foreground">{t.providerLabel}</span>
            <select
              value={provider}
              onChange={(e) => {
                setProvider(e.target.value as LlmProvider);
                setStatus("idle");
                setMessage("");
              }}
              className="w-full rounded-md bg-background px-3 py-2 text-sm outline-none ring-1 ring-border focus:ring-accent"
            >
              {LLM_PROVIDER_IDS.map((id) => (
                <option key={id} value={id}>
                  {LLM_PROVIDERS[id].label}
                </option>
              ))}
            </select>
          </label>

          {/* Model + price */}
          <div className="flex flex-wrap gap-x-6 gap-y-1 rounded-md bg-background px-3 py-2 text-xs ring-1 ring-border">
            <span>
              <span className="text-muted-foreground">{t.modelLabel}: </span>
              <span className="font-mono">{info.model}</span>
            </span>
            <span>
              <span className="text-muted-foreground">{t.priceLabel}: </span>
              <span className="font-mono">
                ${info.inputPrice.toFixed(2)} {t.priceInput} / ${info.outputPrice.toFixed(2)}{" "}
                {t.priceOutput}
              </span>
            </span>
          </div>

          {/* API key */}
          <label className="flex flex-col gap-1">
            <span className="px-1 text-xs text-muted-foreground">{t.keyLabel}</span>
            <input
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder={info.keyPlaceholder}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full rounded-md bg-background px-3 py-2 font-mono text-sm outline-none ring-1 ring-border placeholder:text-muted-foreground/50 focus:ring-accent"
            />
          </label>

          {/* Result message */}
          {message && (
            <p
              className={`text-xs ${status === "success" ? "text-accent" : "text-destructive"}`}
              role="status"
            >
              {message}
            </p>
          )}

          {/* Info section */}
          <section className="rounded-md border border-border/70 bg-background/40 p-3">
            <h3 className="text-xs font-semibold uppercase tracking-tight text-muted-foreground">
              {t.infoTitle}
            </h3>
            <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-normal text-muted-foreground">
              {t.infoPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </section>

          {/* Per-vendor guide */}
          <section className="rounded-md border border-border/70 bg-background/40 p-3">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-xs font-semibold uppercase tracking-tight text-muted-foreground">
                {t.guideTitle} — {info.label}
              </h3>
              <a
                href={info.keyGuideUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-accent hover:underline"
              >
                {t.guideOpenLink} ↗
              </a>
            </div>
            <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs leading-normal text-muted-foreground">
              {guide.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>
        </div>

        {/* Actions */}
        <div className="mt-6 flex items-center justify-between gap-3">
          {hasExistingKey ? (
            <button
              type="button"
              onClick={onRemove}
              disabled={testing}
              className="text-xs font-medium text-destructive hover:underline disabled:opacity-50"
            >
              {t.removeButton}
            </button>
          ) : (
            <span />
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={testing}
              className="rounded-md px-4 py-2 text-sm font-medium text-muted-foreground ring-1 ring-border hover:text-foreground disabled:opacity-50"
            >
              {t.cancelButton}
            </button>
            <button
              type="button"
              onClick={handleTest}
              disabled={testing}
              className="rounded-md bg-primary px-5 py-2 text-sm font-bold text-primary-foreground transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {testing ? t.testingButton : t.testButton}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
