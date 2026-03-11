"""Anvil-specific configuration models for the `anvil` YAML section.

Why:
    The `anvil` section in YAML configures AI providers, GitHub integration,
    variant output, and deployment. These models validate that configuration
    strictly — unknown fields are rejected to catch typos early.
"""

from __future__ import annotations

from typing import Literal

import pydantic

from anvilcv.vendor.rendercv.schema.models.base import BaseModelWithoutExtraKeys


class AnthropicProviderConfig(BaseModelWithoutExtraKeys):
    """Configuration for the Anthropic AI provider."""

    model: str = pydantic.Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model to use for AI features.",
    )
    api_key_env: str = pydantic.Field(
        default="ANTHROPIC_API_KEY",
        description="Environment variable name containing the API key.",
    )


class OpenAIProviderConfig(BaseModelWithoutExtraKeys):
    """Configuration for the OpenAI provider."""

    model: str = pydantic.Field(
        default="gpt-4o",
        description="OpenAI model to use for AI features.",
    )
    api_key_env: str = pydantic.Field(
        default="OPENAI_API_KEY",
        description="Environment variable name containing the API key.",
    )


class OllamaProviderConfig(BaseModelWithoutExtraKeys):
    """Configuration for the Ollama local provider."""

    model: str = pydantic.Field(
        default="llama3.1:8b",
        description="Ollama model to use for AI features.",
    )
    base_url: str = pydantic.Field(
        default="http://localhost:11434",
        description="Ollama server URL.",
    )


class ProvidersConfig(BaseModelWithoutExtraKeys):
    """AI provider configuration."""

    default: Literal["anthropic", "openai", "ollama"] = pydantic.Field(
        default="anthropic",
        description="Default provider when not specified per-command.",
    )
    anthropic: AnthropicProviderConfig = pydantic.Field(
        default_factory=AnthropicProviderConfig,
    )
    openai: OpenAIProviderConfig = pydantic.Field(
        default_factory=OpenAIProviderConfig,
    )
    ollama: OllamaProviderConfig = pydantic.Field(
        default_factory=OllamaProviderConfig,
    )


class GitHubConfig(BaseModelWithoutExtraKeys):
    """GitHub integration configuration."""

    username: str = pydantic.Field(
        description="GitHub username to scan.",
    )
    token_env: str = pydantic.Field(
        default="GITHUB_TOKEN",
        description="Environment variable name containing the GitHub token.",
    )
    include_repos: list[str] = pydantic.Field(
        default_factory=list,
        description="Repos to include (empty = all public repos).",
    )
    exclude_repos: list[str] = pydantic.Field(
        default_factory=list,
        description="Repos to exclude from scan results.",
    )
    include_forks: bool = pydantic.Field(
        default=False,
        description="Whether to include forked repositories.",
    )
    min_stars: int = pydantic.Field(
        default=0,
        ge=0,
        description="Minimum stars for a repo to be included.",
    )
    min_commits: int = pydantic.Field(
        default=5,
        ge=0,
        description="Minimum user commits for a repo to be included.",
    )


class VariantsConfig(BaseModelWithoutExtraKeys):
    """Variant output configuration."""

    output_dir: str = pydantic.Field(
        default="./variants",
        description="Directory where tailored variants are written.",
    )
    naming: str = pydantic.Field(
        default="{name}_{company}_{date}",
        description="Naming template for variant files.",
    )


class DeployConfig(BaseModelWithoutExtraKeys):
    """Deployment configuration."""

    platform: Literal["vercel"] = pydantic.Field(
        default="vercel",
        description="Deployment platform.",
    )
    token_env: str = pydantic.Field(
        default="VERCEL_TOKEN",
        description="Environment variable name containing the deploy token.",
    )
    project_name: str | None = pydantic.Field(
        default=None,
        description="Project name on the deployment platform.",
    )
    domain: str | None = pydantic.Field(
        default=None,
        description="Custom domain for deployment.",
    )


class AnvilConfig(BaseModelWithoutExtraKeys):
    """Top-level Anvil configuration in the `anvil` YAML section."""

    providers: ProvidersConfig = pydantic.Field(
        default_factory=ProvidersConfig,
        description="AI provider configuration.",
    )
    github: GitHubConfig | None = pydantic.Field(
        default=None,
        description="GitHub integration configuration.",
    )
    variants: VariantsConfig = pydantic.Field(
        default_factory=VariantsConfig,
        description="Variant output configuration.",
    )
    deploy: DeployConfig | None = pydantic.Field(
        default=None,
        description="Deployment configuration.",
    )
