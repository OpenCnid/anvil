"""AI provider abstraction: pluggable, not fungible.

Why:
    Different AI providers have fundamentally different APIs, prompt formats,
    and capabilities. Rather than a lowest-common-denominator interface, each
    provider gets its own prompt templates and output parsing. The abstraction
    layer handles the shared concerns: configuration, token budgeting, retry
    logic, and error handling.

    Per design principle P5: "Providers are pluggable not fungible."
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class TaskType(Enum):
    """AI task types that have per-provider prompt templates."""

    TAILOR_BULLETS = "tailor_bullets"
    COVER_LETTER = "cover_letter"
    INTERVIEW_PREP = "interview_prep"
    KEYWORD_EXTRACTION = "keyword_extraction"


@dataclass
class ProviderCapabilities:
    """What a provider can do — used for token budgeting and feature gating."""

    max_context_tokens: int
    max_output_tokens: int
    supports_json_mode: bool
    supports_system_message: bool
    default_model: str
    tested_models: list[str] = field(default_factory=list)


@dataclass
class GenerationRequest:
    """A request to generate text from an AI provider."""

    task: TaskType
    system_prompt: str
    user_prompt: str
    model: str | None = None  # None = use provider default
    max_output_tokens: int | None = None
    temperature: float = 0.3


@dataclass
class GenerationResponse:
    """Response from an AI provider."""

    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    raw_response: dict | None = None


class AIProvider(ABC):
    """Abstract base class for AI providers.

    Each provider implements this interface with its own API client,
    prompt format preferences, and error handling.
    """

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Return this provider's capabilities for token budgeting."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text from a prompt. Raises AnvilAIProviderError on failure."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this provider has the necessary API keys/config."""

    @abstractmethod
    def get_setup_instructions(self) -> str:
        """Return user-facing instructions for configuring this provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'anthropic', 'openai', 'ollama')."""
