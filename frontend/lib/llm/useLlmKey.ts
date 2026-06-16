"use client";

import { useCallback, useSyncExternalStore } from "react";
import { isLlmProvider, type LlmProvider } from "./providers";

const STORAGE_KEY = "sm.llmCredentials";
// Same-tab broadcast so independent hook instances (form + modal + audit flow)
// stay in sync; the native "storage" event only fires in *other* tabs.
const SYNC_EVENT = "sm:llm-credentials";

export interface LlmCredentials {
  provider: LlmProvider;
  apiKey: string;
}

function parse(raw: string | null): LlmCredentials | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<LlmCredentials>;
    if (
      parsed &&
      typeof parsed.apiKey === "string" &&
      parsed.apiKey.length > 0 &&
      isLlmProvider(parsed.provider)
    ) {
      return { provider: parsed.provider, apiKey: parsed.apiKey };
    }
  } catch {
    // Corrupt value — treat as not configured.
  }
  return null;
}

// useSyncExternalStore requires a referentially-stable snapshot while the
// underlying value is unchanged; cache the parsed result keyed by the raw string.
let cachedRaw: string | null = null;
let cachedValue: LlmCredentials | null = null;

function getSnapshot(): LlmCredentials | null {
  const raw =
    typeof window === "undefined" ? null : window.localStorage.getItem(STORAGE_KEY);
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    cachedValue = parse(raw);
  }
  return cachedValue;
}

function getServerSnapshot(): LlmCredentials | null {
  return null;
}

function subscribe(onChange: () => void): () => void {
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) onChange();
  };
  window.addEventListener(SYNC_EVENT, onChange);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(SYNC_EVENT, onChange);
    window.removeEventListener("storage", onStorage);
  };
}

export interface UseLlmKey {
  credentials: LlmCredentials | null;
  isConfigured: boolean;
  save: (next: LlmCredentials) => void;
  clear: () => void;
}

export function useLlmKey(): UseLlmKey {
  const credentials = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const save = useCallback((next: LlmCredentials) => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    window.dispatchEvent(new Event(SYNC_EVENT));
  }, []);

  const clear = useCallback(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new Event(SYNC_EVENT));
  }, []);

  return { credentials, isConfigured: credentials !== null, save, clear };
}
