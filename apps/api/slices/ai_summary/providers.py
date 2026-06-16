from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LLMProvider = Literal["openai", "gemini", "anthropic", "openrouter"]

LLMFamily = Literal["openai", "anthropic"]


@dataclass(frozen=True)
class ProviderConfig:
    """Static, auditable configuration for one supported provider."""

    provider: LLMProvider
    label: str
    base_url: str
    model: str
    family: LLMFamily


PROVIDERS: dict[LLMProvider, ProviderConfig] = {
    "openai": ProviderConfig(
        provider="openai",
        label="OpenAI",
        base_url="https://api.openai.com/v1",
        model="gpt-5.4-mini",
        family="openai",
    ),
    "gemini": ProviderConfig(
        provider="gemini",
        label="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        model="gemini-2.5-flash",
        family="openai",
    ),
    "anthropic": ProviderConfig(
        provider="anthropic",
        label="Anthropic",
        base_url="https://api.anthropic.com/v1",
        model="claude-haiku-4-5-20251001",
        family="anthropic",
    ),
    "openrouter": ProviderConfig(
        provider="openrouter",
        label="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        model="google/gemini-2.5-flash",
        family="openai",
    ),
}


@dataclass(frozen=True)
class LLMCredentials:
    """A user-supplied provider + API key for a single request.

    Carries a secret that lives only in the user's browser and is passed
    transiently via the ``X-LLM-Api-Key`` header. Never log it, and never store
    it on ``AuditRequest``/``AuditReport`` (those get persisted).
    """

    provider: LLMProvider
    api_key: str

    @property
    def config(self) -> ProviderConfig:
        return PROVIDERS[self.provider]
