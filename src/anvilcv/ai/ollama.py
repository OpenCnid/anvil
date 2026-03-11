"""Ollama AI provider implementation.

Why:
    Ollama runs models locally with no authentication or rate limits.
    Smaller models (8B params) have limited context windows (~8K tokens)
    and need simplified prompts. The tested set is llama3.1:8b and
    llama3.1:70b; other models are accepted with a warning.
"""

import logging

import httpx

from anvilcv.ai.provider import (
    AIProvider,
    GenerationRequest,
    GenerationResponse,
    ProviderCapabilities,
)
from anvilcv.exceptions import AnvilAIProviderError

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "llama3.1:8b"
_TESTED_MODELS = ["llama3.1:8b", "llama3.1:70b"]
_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(AIProvider):
    """Ollama provider for local model inference."""

    def __init__(self, model: str | None = None, base_url: str | None = None):
        self._model = model or _DEFAULT_MODEL
        self._base_url = base_url or _DEFAULT_BASE_URL

    @property
    def name(self) -> str:
        return "ollama"

    def get_capabilities(self) -> ProviderCapabilities:
        # Context window depends on model size; 8K is conservative for 8B models
        return ProviderCapabilities(
            max_context_tokens=8_192,
            max_output_tokens=4_096,
            supports_json_mode=False,  # Partial support, not reliable
            supports_system_message=True,
            default_model=_DEFAULT_MODEL,
            tested_models=_TESTED_MODELS,
        )

    def is_configured(self) -> bool:
        # Ollama doesn't need an API key; check if server is reachable
        try:
            response = httpx.get(f"{self._base_url}/api/version", timeout=2.0)
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def get_setup_instructions(self) -> str:
        return (
            "To use Ollama (local AI):\n"
            "  1. Install Ollama: https://ollama.ai/download\n"
            "  2. Start the server: ollama serve\n"
            "  3. Pull a model: ollama pull llama3.1:8b\n"
            "  4. AnvilCV will automatically detect it at localhost:11434"
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        model = request.model or self._model

        if model not in _TESTED_MODELS:
            logger.warning(
                "Model '%s' is not in the tested set %s. Results may vary.",
                model,
                _TESTED_MODELS,
            )

        # Combine system and user prompts for Ollama's chat API
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": request.temperature,
            },
        }

        if request.max_output_tokens:
            payload["options"]["num_predict"] = request.max_output_tokens

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)

            if response.status_code != 200:
                raise AnvilAIProviderError(
                    message=(
                        f"Ollama returned HTTP {response.status_code}.\n"
                        f"Response: {response.text[:500]}"
                    )
                )

            data = response.json()
            content = data.get("message", {}).get("content", "")

            return GenerationResponse(
                content=content,
                model=model,
                provider=self.name,
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
                raw_response=data,
            )

        except httpx.ConnectError as e:
            raise AnvilAIProviderError(
                message=(
                    f"Cannot connect to Ollama at {self._base_url}.\n"
                    f"Is Ollama running? Start with: ollama serve\n\n{e}"
                )
            ) from e
        except httpx.TimeoutException as e:
            raise AnvilAIProviderError(
                message=(
                    "Ollama request timed out. The model may be loading or "
                    "the prompt may be too large for this model.\n"
                    f"Details: {e}"
                )
            ) from e
        except AnvilAIProviderError:
            raise
        except Exception as e:
            raise AnvilAIProviderError(
                message=f"Unexpected error calling Ollama: {e}"
            ) from e
