"""OpenAI AI provider implementation.

Why:
    OpenAI's GPT models support native JSON mode and structured outputs.
    This provider uses the Chat Completions API with JSON mode when available,
    falling back to plain text for models that don't support it.
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

_DEFAULT_MODEL = "gpt-4o"
_TESTED_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]


class OpenAIProvider(AIProvider):
    """OpenAI provider using the Chat Completions API."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model or _DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "openai"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            max_context_tokens=128_000,
            max_output_tokens=16_384,
            supports_json_mode=True,
            supports_system_message=True,
            default_model=_DEFAULT_MODEL,
            tested_models=_TESTED_MODELS,
        )

    def is_configured(self) -> bool:
        return self._api_key is not None and len(self._api_key) > 0

    def get_setup_instructions(self) -> str:
        return (
            "To use OpenAI:\n"
            "  1. Get an API key at https://platform.openai.com/api-keys\n"
            "  2. Set the environment variable:\n"
            "     export OPENAI_API_KEY='your-key-here'\n"
            "  3. Or add to .anvil/config.yaml:\n"
            "     providers:\n"
            "       openai:\n"
            "         api_key_env: OPENAI_API_KEY"
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self.is_configured():
            raise AnvilAIProviderError(
                message=f"OpenAI API key not configured.\n\n{self.get_setup_instructions()}"
            )

        try:
            import openai  # noqa: PLC0415
        except ImportError:
            raise AnvilAIProviderError(
                message=('OpenAI SDK not installed. Install with:\n  pip install "anvilcv[ai]"')
            ) from None

        model = request.model or self._model
        max_tokens = request.max_output_tokens or self.get_capabilities().max_output_tokens

        try:
            client = openai.OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
                temperature=request.temperature,
            )

            choice = response.choices[0]
            content = choice.message.content or ""

            return GenerationResponse(
                content=content,
                model=model,
                provider=self.name,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                raw_response={"id": response.id, "finish_reason": choice.finish_reason},
            )

        except openai.AuthenticationError as e:
            raise AnvilAIProviderError(
                message=f"OpenAI authentication failed. Check your API key.\n{e}"
            ) from e
        except openai.RateLimitError as e:
            raise AnvilAIProviderError(
                message=(f"OpenAI rate limit exceeded. Wait a moment and try again.\nDetails: {e}")
            ) from e
        except openai.APIError as e:
            raise AnvilAIProviderError(message=f"OpenAI API error: {e}") from e
        except Exception as e:
            raise AnvilAIProviderError(message=f"Unexpected error calling OpenAI: {e}") from e
