"""Anthropic AI provider implementation.

Why:
    Anthropic's Claude models use XML-structured prompts and have a separate
    system message parameter. This provider implements the Anthropic-specific
    API patterns: XML output tags, tier-dependent rate limits, and the
    Messages API with proper error handling.
"""

import logging
import os

from anvilcv.ai.provider import (
    AIProvider,
    GenerationRequest,
    GenerationResponse,
    ProviderCapabilities,
)
from anvilcv.exceptions import AnvilAIProviderError

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_TESTED_MODELS = ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"]


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider using the Messages API."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._model = model or _DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "anthropic"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            max_context_tokens=200_000,
            max_output_tokens=8_192,
            supports_json_mode=False,  # Uses XML-structured output instead
            supports_system_message=True,
            default_model=_DEFAULT_MODEL,
            tested_models=_TESTED_MODELS,
        )

    def is_configured(self) -> bool:
        return self._api_key is not None and len(self._api_key) > 0

    def get_setup_instructions(self) -> str:
        return (
            "To use Anthropic Claude:\n"
            "  1. Get an API key at https://console.anthropic.com/\n"
            "  2. Set the environment variable:\n"
            "     export ANTHROPIC_API_KEY='your-key-here'\n"
            "  3. Or add to .anvil/config.yaml:\n"
            "     providers:\n"
            "       anthropic:\n"
            "         api_key_env: ANTHROPIC_API_KEY"
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self.is_configured():
            raise AnvilAIProviderError(
                message=f"Anthropic API key not configured.\n\n{self.get_setup_instructions()}"
            )

        try:
            import anthropic  # noqa: PLC0415
        except ImportError:
            raise AnvilAIProviderError(
                message=(
                    "Anthropic SDK not installed. Install with:\n"
                    '  pip install "anvilcv[ai]"'
                )
            ) from None

        model = request.model or self._model
        max_tokens = request.max_output_tokens or self.get_capabilities().max_output_tokens

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=request.system_prompt,
                messages=[{"role": "user", "content": request.user_prompt}],
                temperature=request.temperature,
            )

            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return GenerationResponse(
                content=content,
                model=model,
                provider=self.name,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                raw_response={"id": response.id, "stop_reason": response.stop_reason},
            )

        except anthropic.AuthenticationError as e:
            raise AnvilAIProviderError(
                message=f"Anthropic authentication failed. Check your API key.\n{e}"
            ) from e
        except anthropic.RateLimitError as e:
            raise AnvilAIProviderError(
                message=(
                    "Anthropic rate limit exceeded. Wait a moment and try again.\n"
                    f"Details: {e}"
                )
            ) from e
        except anthropic.APIError as e:
            raise AnvilAIProviderError(
                message=f"Anthropic API error: {e}"
            ) from e
        except Exception as e:
            raise AnvilAIProviderError(
                message=f"Unexpected error calling Anthropic: {e}"
            ) from e
