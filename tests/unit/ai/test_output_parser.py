"""Tests for AI output parser — retry logic, code block extraction, debug logging.

Why:
    AI responses are non-deterministic. The output parser must correctly extract
    content from various code block formats, handle retries per provider policy
    (1 retry for Anthropic/OpenAI, 3 for Ollama), and save debug logs when
    all retries are exhausted.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from anvilcv.ai.output_parser import (
    generate_with_retry,
    parse_json_from_response,
    parse_yaml_from_response,
)
from anvilcv.ai.provider import GenerationRequest, GenerationResponse, TaskType
from anvilcv.exceptions import AnvilAIProviderError


class TestParseYamlFromResponse:
    """YAML extraction from various AI response formats."""

    def test_raw_yaml(self):
        assert parse_yaml_from_response("key: value\n") == "key: value"

    def test_yaml_code_block(self):
        content = "Here is the YAML:\n```yaml\nkey: value\nlist:\n  - item\n```\nDone."
        assert parse_yaml_from_response(content) == "key: value\nlist:\n  - item"

    def test_generic_code_block(self):
        """Generic ``` blocks should also be extracted (covers lines 47-52)."""
        content = "```\nkey: value\n```"
        assert parse_yaml_from_response(content) == "key: value"

    def test_generic_code_block_with_language(self):
        """Generic code block with language identifier on first line."""
        content = "```yml\nkey: value\nother: 2\n```"
        assert parse_yaml_from_response(content) == "key: value\nother: 2"

    def test_unclosed_yaml_code_block(self):
        """Unclosed code block should extract to end of content."""
        content = "```yaml\nkey: value\nno closing"
        assert parse_yaml_from_response(content) == "key: value\nno closing"

    def test_unclosed_generic_code_block(self):
        """Unclosed generic code block extracts to end."""
        content = "```\nkey: value"
        # Start is at index 3, newline after ``` is at index 3
        result = parse_yaml_from_response(content)
        assert "key: value" in result

    def test_whitespace_only(self):
        assert parse_yaml_from_response("   \n  ") == ""


class TestParseJsonFromResponse:
    """JSON extraction from various AI response formats."""

    def test_raw_json(self):
        result = parse_json_from_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_code_block(self):
        content = '```json\n{"key": "value"}\n```'
        result = parse_json_from_response(content)
        assert result == {"key": "value"}

    def test_generic_code_block_json(self):
        """Generic ``` blocks with JSON inside (covers lines 66-70)."""
        content = '```\n{"key": "value"}\n```'
        result = parse_json_from_response(content)
        assert result == {"key": "value"}

    def test_invalid_json(self):
        result = parse_json_from_response("not json at all")
        assert result is None

    def test_invalid_json_in_code_block(self):
        content = "```json\n{broken json\n```"
        result = parse_json_from_response(content)
        assert result is None

    def test_unclosed_json_code_block(self):
        content = '```json\n{"key": "value"}'
        result = parse_json_from_response(content)
        assert result == {"key": "value"}

    def test_generic_code_block_with_language_json(self):
        content = '```javascript\n{"key": "value"}\n```'
        result = parse_json_from_response(content)
        assert result == {"key": "value"}


class TestGenerateWithRetry:
    """Retry logic with provider-specific retry counts."""

    def _make_request(self) -> GenerationRequest:
        return GenerationRequest(
            task=TaskType.TAILOR_BULLETS,
            system_prompt="test",
            user_prompt="test",
            model="test-model",
        )

    def test_success_on_first_try(self):
        response = GenerationResponse(content="good", model="m", provider="p")
        gen_fn = AsyncMock(return_value=response)

        result = asyncio.run(
            generate_with_retry(gen_fn, self._make_request(), "anthropic")
        )
        assert result.content == "good"
        assert gen_fn.call_count == 1

    def test_success_with_validator(self):
        response = GenerationResponse(content="valid", model="m", provider="p")
        gen_fn = AsyncMock(return_value=response)

        result = asyncio.run(
            generate_with_retry(
                gen_fn,
                self._make_request(),
                "anthropic",
                validate_fn=lambda c: c == "valid",
            )
        )
        assert result.content == "valid"

    def test_retry_on_validation_failure_anthropic(self):
        """Anthropic gets 1 retry (2 total attempts)."""
        bad = GenerationResponse(content="bad", model="m", provider="p")
        good = GenerationResponse(content="good", model="m", provider="p")
        gen_fn = AsyncMock(side_effect=[bad, good])

        result = asyncio.run(
            generate_with_retry(
                gen_fn,
                self._make_request(),
                "anthropic",
                validate_fn=lambda c: c == "good",
            )
        )
        assert result.content == "good"
        assert gen_fn.call_count == 2

    def test_retry_on_validation_failure_ollama(self):
        """Ollama gets 3 retries (4 total attempts)."""
        bad = GenerationResponse(content="bad", model="m", provider="p")
        good = GenerationResponse(content="good", model="m", provider="p")
        gen_fn = AsyncMock(side_effect=[bad, bad, bad, good])

        result = asyncio.run(
            generate_with_retry(
                gen_fn,
                self._make_request(),
                "ollama",
                validate_fn=lambda c: c == "good",
            )
        )
        assert result.content == "good"
        assert gen_fn.call_count == 4

    @patch("anvilcv.ai.output_parser.save_debug_log")
    def test_all_retries_exhausted_raises(self, mock_save_debug):
        """When all retries fail, saves debug log and raises (covers lines 130-149)."""
        mock_save_debug.return_value = "/tmp/debug.json"
        bad = GenerationResponse(content="bad", model="m", provider="p")
        gen_fn = AsyncMock(return_value=bad)

        with pytest.raises(AnvilAIProviderError, match="failed validation"):
            asyncio.run(
                generate_with_retry(
                    gen_fn,
                    self._make_request(),
                    "anthropic",
                    validate_fn=lambda c: False,  # Always fails
                )
            )

        mock_save_debug.assert_called_once()
        debug_data = mock_save_debug.call_args[1]["data"]
        assert debug_data["provider"] == "anthropic"
        assert debug_data["attempts"] == 2
        assert debug_data["last_content"] == "bad"

    @patch("anvilcv.ai.output_parser.save_debug_log")
    def test_exception_retries_then_raises(self, mock_save_debug):
        """Exceptions (not AnvilAIProviderError) are retried (covers lines 120-128)."""
        mock_save_debug.return_value = "/tmp/debug.json"
        gen_fn = AsyncMock(side_effect=RuntimeError("network error"))

        with pytest.raises(AnvilAIProviderError, match="failed validation"):
            asyncio.run(
                generate_with_retry(
                    gen_fn,
                    self._make_request(),
                    "openai",
                )
            )

        # openai gets 1 retry = 2 total attempts
        assert gen_fn.call_count == 2
        debug_data = mock_save_debug.call_args[1]["data"]
        assert debug_data["last_error"] == "network error"

    def test_ai_provider_error_not_retried(self):
        """AnvilAIProviderError (auth/rate-limit) should NOT be retried (line 118-119)."""
        gen_fn = AsyncMock(
            side_effect=AnvilAIProviderError(message="rate limited")
        )

        with pytest.raises(AnvilAIProviderError, match="rate limited"):
            asyncio.run(
                generate_with_retry(
                    gen_fn,
                    self._make_request(),
                    "anthropic",
                )
            )

        assert gen_fn.call_count == 1  # No retry

    def test_unknown_provider_gets_1_retry(self):
        """Unknown providers default to 1 retry."""
        bad = GenerationResponse(content="bad", model="m", provider="p")
        good = GenerationResponse(content="good", model="m", provider="p")
        gen_fn = AsyncMock(side_effect=[bad, good])

        result = asyncio.run(
            generate_with_retry(
                gen_fn,
                self._make_request(),
                "unknown_provider",
                validate_fn=lambda c: c == "good",
            )
        )
        assert result.content == "good"
        assert gen_fn.call_count == 2
