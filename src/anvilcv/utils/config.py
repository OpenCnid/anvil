"""Configuration management: API keys, .anvil/config.yaml, provider resolution.

Why:
    Anvil's AI features need API keys and provider configuration. This module
    centralizes config resolution so every command uses the same lookup chain:
    CLI flag → environment variable → .anvil/config.yaml → sensible default.

    The .anvil/ directory convention keeps project-local config separate from
    the resume YAML (which stays the source of truth per design principle P1).
"""

import os
import pathlib
from typing import Any

from ruamel.yaml import YAML


def get_anvil_dir(base_path: pathlib.Path | None = None) -> pathlib.Path:
    """Return the .anvil/ directory path, creating it if it doesn't exist."""
    base = base_path or pathlib.Path.cwd()
    anvil_dir = base / ".anvil"
    anvil_dir.mkdir(exist_ok=True)
    return anvil_dir


def load_config(base_path: pathlib.Path | None = None) -> dict[str, Any]:
    """Load .anvil/config.yaml if it exists, otherwise return empty dict."""
    anvil_dir = get_anvil_dir(base_path)
    config_file = anvil_dir / "config.yaml"
    if config_file.exists():
        yaml = YAML()
        data = yaml.load(config_file)
        return dict(data) if data else {}
    return {}


_ENV_VAR_MAP: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def get_api_key(provider: str, config: dict[str, Any] | None = None) -> str | None:
    """Look up API key for a provider.

    Resolution order:
        1. Standard environment variable (e.g. ANTHROPIC_API_KEY)
        2. Custom env var from .anvil/config.yaml ``providers.<name>.api_key_env``
    """
    # Standard env var
    env_var = _ENV_VAR_MAP.get(provider)
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key

    # Custom env var from config
    if config:
        provider_config = config.get("providers", {}).get(provider, {})
        custom_env = provider_config.get("api_key_env")
        if custom_env:
            key = os.environ.get(custom_env)
            if key:
                return key

    return None


def resolve_provider(
    config: dict[str, Any] | None = None,
    cli_provider: str | None = None,
) -> str | None:
    """Determine which AI provider to use.

    Resolution order:
        1. CLI ``--provider`` flag
        2. ``config.yaml`` default provider
        3. First configured provider with an API key available
    """
    if cli_provider:
        return cli_provider

    if config:
        default: str | None = config.get("providers", {}).get("default")
        if default:
            return default

    # Auto-detect: first provider with an API key, or ollama (no key needed)
    for provider in ("anthropic", "openai"):
        if get_api_key(provider, config):
            return provider

    return None
