"""AI output parser with retry logic and debug logging.

Why:
    AI responses are non-deterministic and may not conform to the expected
    schema. This module validates responses, retries on malformed output
    (1 retry for Anthropic/OpenAI, 3 for Ollama), and saves failed responses
    to .anvil/debug/ for troubleshooting.

    Per spec: "Malformed response: Warning + retries (1x Anthropic/OpenAI,
    3x Ollama) + debug log."
"""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from anvilcv.ai.provider import GenerationRequest, GenerationResponse
from anvilcv.exceptions import AnvilAIProviderError
from anvilcv.utils.cache import save_debug_log

logger = logging.getLogger(__name__)

# Retry counts per provider
_MAX_RETRIES: dict[str, int] = {
    "anthropic": 1,
    "openai": 1,
    "ollama": 3,
}


def parse_yaml_from_response(content: str) -> str | None:
    """Extract YAML content from an AI response.

    Handles responses wrapped in ```yaml ... ``` code blocks
    or raw YAML content.
    """
    content = content.strip()

    # Try to extract from code block
    if "```yaml" in content:
        start = content.index("```yaml") + 7
        end = content.index("```", start) if "```" in content[start:] else len(content)
        return content[start:end].strip()

    if "```" in content:
        start = content.index("```") + 3
        # Skip language identifier on same line
        newline = content.index("\n", start) if "\n" in content[start:] else start
        end = content.index("```", newline) if "```" in content[newline:] else len(content)
        return content[newline:end].strip()

    return content


def parse_json_from_response(content: str) -> dict[str, Any] | None:
    """Extract JSON from an AI response."""
    content = content.strip()

    # Try to extract from code block
    if "```json" in content:
        start = content.index("```json") + 7
        end = content.index("```", start) if "```" in content[start:] else len(content)
        content = content[start:end].strip()
    elif "```" in content:
        start = content.index("```") + 3
        newline = content.index("\n", start) if "\n" in content[start:] else start
        end = content.index("```", newline) if "```" in content[newline:] else len(content)
        content = content[newline:end].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


async def generate_with_retry(
    generate_fn: Callable[[GenerationRequest], Awaitable[GenerationResponse]],
    request: GenerationRequest,
    provider_name: str,
    validate_fn: Callable[[str], bool] | None = None,
) -> GenerationResponse:
    """Call generate_fn with retry logic for malformed responses.

    Args:
        generate_fn: The provider's generate method.
        request: The generation request.
        provider_name: Provider name for retry count lookup.
        validate_fn: Optional validator; if it returns False, retry.

    Returns:
        The first valid response.

    Raises:
        AnvilAIProviderError: If all retries fail.
    """
    max_retries = _MAX_RETRIES.get(provider_name, 1)
    last_error: Exception | None = None
    last_content: str = ""

    for attempt in range(max_retries + 1):
        try:
            response = await generate_fn(request)
            last_content = response.content

            if validate_fn is None or validate_fn(response.content):
                return response

            logger.warning(
                "Response from %s failed validation (attempt %d/%d)",
                provider_name,
                attempt + 1,
                max_retries + 1,
            )

        except AnvilAIProviderError:
            raise  # Don't retry on auth/rate-limit errors
        except Exception as e:
            last_error = e
            logger.warning(
                "Error from %s (attempt %d/%d): %s",
                provider_name,
                attempt + 1,
                max_retries + 1,
                e,
            )

    # All retries exhausted — save debug log
    debug_data = {
        "provider": provider_name,
        "task": request.task.value,
        "model": request.model,
        "attempts": max_retries + 1,
        "last_content": last_content[:2000],  # Truncate for debug log
        "last_error": str(last_error) if last_error else None,
        "timestamp": time.time(),
    }
    filename = f"failed_{provider_name}_{int(time.time())}.json"
    debug_file = save_debug_log(filename=filename, data=debug_data)
    logger.error("All retries exhausted. Debug log saved to %s", debug_file)

    raise AnvilAIProviderError(
        message=(
            f"AI response from {provider_name} failed validation after "
            f"{max_retries + 1} attempts. Debug log saved to {debug_file}"
        )
    )
