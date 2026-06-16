// Single source of truth for the supported LLM providers shown in the UI.
// Facts only (model, prices, key location) — translatable copy lives in i18n
// (dict.apiKeyModal). The model is fixed per provider and must match the
// backend registry in apps/api/slices/ai_summary/providers.py.
//
// Prices are USD per 1,000,000 tokens (list price). Sources (fetched 2026-06):
//   - OpenAI GPT-5.4 mini       — openrouter.ai/openai/gpt-5.4-mini
//   - Gemini 2.5 Flash          — ai.google.dev/gemini-api/docs/pricing
//   - Anthropic Claude Haiku 4.5 — platform.claude.com pricing
//   - OpenRouter Gemini 2.5 Flash — openrouter.ai/google/gemini-2.5-flash

export type LlmProvider = "openai" | "gemini" | "anthropic" | "openrouter";

export interface LlmProviderInfo {
  id: LlmProvider;
  /** Brand name — not translated. */
  label: string;
  /** Human model name — not translated. */
  model: string;
  /** USD per 1M input tokens. */
  inputPrice: number;
  /** USD per 1M output tokens. */
  outputPrice: number;
  /** Where the user creates an API key. */
  keyGuideUrl: string;
  /** Placeholder hint for the key field. */
  keyPlaceholder: string;
}

export const LLM_PROVIDERS: Record<LlmProvider, LlmProviderInfo> = {
  openai: {
    id: "openai",
    label: "OpenAI",
    model: "GPT-5.4 mini",
    inputPrice: 0.75,
    outputPrice: 4.5,
    keyGuideUrl: "https://platform.openai.com/api-keys",
    keyPlaceholder: "sk-...",
  },
  gemini: {
    id: "gemini",
    label: "Google Gemini",
    model: "Gemini 2.5 Flash",
    inputPrice: 0.3,
    outputPrice: 2.5,
    keyGuideUrl: "https://aistudio.google.com/apikey",
    keyPlaceholder: "AIza...",
  },
  anthropic: {
    id: "anthropic",
    label: "Anthropic",
    model: "Claude Haiku 4.5",
    inputPrice: 1.0,
    outputPrice: 5.0,
    keyGuideUrl: "https://console.anthropic.com/settings/keys",
    keyPlaceholder: "sk-ant-...",
  },
  openrouter: {
    id: "openrouter",
    label: "OpenRouter",
    model: "Gemini 2.5 Flash (via OpenRouter)",
    inputPrice: 0.3,
    outputPrice: 2.5,
    keyGuideUrl: "https://openrouter.ai/keys",
    keyPlaceholder: "sk-or-...",
  },
};

export const LLM_PROVIDER_IDS = Object.keys(LLM_PROVIDERS) as LlmProvider[];

export function isLlmProvider(value: unknown): value is LlmProvider {
  return typeof value === "string" && value in LLM_PROVIDERS;
}
