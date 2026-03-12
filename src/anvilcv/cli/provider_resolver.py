"""Shared AI provider resolution for CLI commands.

Why:
    The tailor, cover, and prep commands all need to resolve an AI provider
    from CLI flags and YAML config. This module eliminates the duplicated
    _resolve_provider() function across those commands.
"""

from __future__ import annotations

from anvilcv.ai.provider import AIProvider
from anvilcv.exceptions import AnvilAIProviderError, AnvilUserError


def resolve_provider(
    provider_name: str | None = None,
    model_name: str | None = None,
    resume_data: dict | None = None,
) -> AIProvider:
    """Resolve which AI provider to use.

    Priority: CLI --provider flag > YAML config > default (anthropic).
    """
    from anvilcv.ai.anthropic import AnthropicProvider
    from anvilcv.ai.ollama import OllamaProvider
    from anvilcv.ai.openai import OpenAIProvider

    anvil_config = (resume_data or {}).get("anvil", {})
    providers_config = anvil_config.get("providers", {})

    if provider_name is None:
        provider_name = providers_config.get("default", "anthropic")

    provider_map = {
        "anthropic": lambda: AnthropicProvider(
            model=model_name or providers_config.get("anthropic", {}).get("model"),
        ),
        "openai": lambda: OpenAIProvider(
            model=model_name or providers_config.get("openai", {}).get("model"),
        ),
        "ollama": lambda: OllamaProvider(
            model=model_name or providers_config.get("ollama", {}).get("model"),
            base_url=providers_config.get("ollama", {}).get("base_url"),
        ),
    }

    factory = provider_map.get(provider_name)
    if factory is None:
        raise AnvilUserError(
            message=f"Unknown provider: {provider_name}. Supported: anthropic, openai, ollama"
        )

    provider = factory()
    if not provider.is_configured():
        instructions = provider.get_setup_instructions()
        raise AnvilAIProviderError(
            message=f"Provider {provider_name} is not configured.\n{instructions}"
        )

    return provider
