"""Tests for AI providers with mocked API responses.

Why:
    AI providers are the bridge to external APIs. We test with mocks to verify:
    - Correct request formatting per provider
    - Proper error handling (auth failures, rate limits, malformed responses)
    - Response parsing and token counting
    - Configuration detection (is_configured)
    These run in CI without API keys.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from anvilcv.ai.anthropic import AnthropicProvider
from anvilcv.ai.ollama import OllamaProvider
from anvilcv.ai.openai import OpenAIProvider
from anvilcv.ai.provider import GenerationRequest, TaskType
from anvilcv.exceptions import AnvilAIProviderError

# --- Provider Capabilities ---


class TestProviderCapabilities:
    def test_anthropic_capabilities(self):
        provider = AnthropicProvider(api_key="test")
        caps = provider.get_capabilities()
        assert caps.max_context_tokens == 200_000
        assert caps.max_output_tokens == 8_192
        assert caps.supports_system_message is True
        assert caps.supports_json_mode is False
        assert "claude-sonnet-4-20250514" in caps.tested_models

    def test_openai_capabilities(self):
        provider = OpenAIProvider(api_key="test")
        caps = provider.get_capabilities()
        assert caps.max_context_tokens == 128_000
        assert caps.supports_json_mode is True
        assert "gpt-4o" in caps.tested_models

    def test_ollama_capabilities(self):
        provider = OllamaProvider()
        caps = provider.get_capabilities()
        assert caps.max_context_tokens == 8_192
        assert "llama3.1:8b" in caps.tested_models


# --- Configuration Detection ---


class TestProviderConfiguration:
    def test_anthropic_configured_with_key(self):
        assert AnthropicProvider(api_key="sk-test").is_configured() is True

    def test_anthropic_not_configured(self):
        assert AnthropicProvider(api_key="").is_configured() is False
        assert AnthropicProvider(api_key=None).is_configured() is False

    def test_anthropic_configured_from_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env-test")
        assert AnthropicProvider().is_configured() is True

    def test_openai_configured_with_key(self):
        assert OpenAIProvider(api_key="sk-test").is_configured() is True

    def test_openai_not_configured(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert OpenAIProvider(api_key="").is_configured() is False

    def test_ollama_not_configured_when_server_down(self):
        # Ollama checks server connectivity
        provider = OllamaProvider(base_url="http://localhost:99999")
        assert provider.is_configured() is False


# --- Setup Instructions ---


class TestSetupInstructions:
    def test_anthropic_instructions(self):
        instructions = AnthropicProvider().get_setup_instructions()
        assert "ANTHROPIC_API_KEY" in instructions
        assert "console.anthropic.com" in instructions

    def test_openai_instructions(self):
        instructions = OpenAIProvider().get_setup_instructions()
        assert "OPENAI_API_KEY" in instructions

    def test_ollama_instructions(self):
        instructions = OllamaProvider().get_setup_instructions()
        assert "ollama" in instructions.lower()


# --- Provider Names ---


class TestProviderNames:
    def test_names(self):
        assert AnthropicProvider(api_key="test").name == "anthropic"
        assert OpenAIProvider(api_key="test").name == "openai"
        assert OllamaProvider().name == "ollama"


# --- Generation with Mocked APIs ---


def _make_request() -> GenerationRequest:
    return GenerationRequest(
        task=TaskType.TAILOR_BULLETS,
        system_prompt="You are a resume expert.",
        user_prompt="Improve this bullet point: Built services.",
        temperature=0.3,
    )


def _mock_anthropic_module():
    """Create a mock anthropic module for sys.modules injection."""
    mock = MagicMock()
    mock.AuthenticationError = type("AuthenticationError", (Exception,), {})
    mock.RateLimitError = type("RateLimitError", (Exception,), {})
    mock.APIError = type("APIError", (Exception,), {})
    return mock


def _mock_openai_module():
    """Create a mock openai module for sys.modules injection."""
    mock = MagicMock()
    mock.AuthenticationError = type("AuthenticationError", (Exception,), {})
    mock.RateLimitError = type("RateLimitError", (Exception,), {})
    mock.APIError = type("APIError", (Exception,), {})
    return mock


class TestAnthropicGeneration:
    def test_generate_success(self):
        provider = AnthropicProvider(api_key="sk-test")
        request = _make_request()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Improved bullet point text")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_response.id = "msg_123"
        mock_response.stop_reason = "end_turn"

        mock_mod = _mock_anthropic_module()
        mock_mod.Anthropic.return_value.messages.create.return_value = mock_response

        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            result = asyncio.run(provider.generate(request))

        assert result.content == "Improved bullet point text"
        assert result.provider == "anthropic"
        assert result.input_tokens == 100
        assert result.output_tokens == 50

    def test_generate_missing_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        provider = AnthropicProvider(api_key=None)
        request = _make_request()

        with pytest.raises(AnvilAIProviderError, match="not configured"):
            asyncio.run(provider.generate(request))

    def test_generate_auth_error(self):
        provider = AnthropicProvider(api_key="sk-invalid")
        request = _make_request()

        mock_mod = _mock_anthropic_module()
        mock_mod.Anthropic.return_value.messages.create.side_effect = mock_mod.AuthenticationError(
            "Invalid API key"
        )

        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            with pytest.raises(AnvilAIProviderError, match="authentication failed"):
                asyncio.run(provider.generate(request))

    def test_generate_rate_limit(self):
        provider = AnthropicProvider(api_key="sk-test")
        request = _make_request()

        mock_mod = _mock_anthropic_module()
        mock_mod.Anthropic.return_value.messages.create.side_effect = mock_mod.RateLimitError(
            "Rate limit exceeded"
        )

        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            with pytest.raises(AnvilAIProviderError, match="rate limit"):
                asyncio.run(provider.generate(request))


class TestOpenAIGeneration:
    def test_generate_success(self):
        provider = OpenAIProvider(api_key="sk-test")
        request = _make_request()

        mock_choice = MagicMock()
        mock_choice.message.content = "Enhanced bullet point"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock(prompt_tokens=80, completion_tokens=40)
        mock_response.id = "chatcmpl-123"

        mock_mod = _mock_openai_module()
        mock_mod.OpenAI.return_value.chat.completions.create.return_value = mock_response

        with patch.dict("sys.modules", {"openai": mock_mod}):
            result = asyncio.run(provider.generate(request))

        assert result.content == "Enhanced bullet point"
        assert result.provider == "openai"
        assert result.input_tokens == 80

    def test_generate_missing_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAIProvider(api_key=None)
        with pytest.raises(AnvilAIProviderError, match="not configured"):
            asyncio.run(provider.generate(_make_request()))


class TestOllamaGeneration:
    def test_generate_success(self):
        provider = OllamaProvider()
        request = _make_request()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Local model response"},
            "prompt_eval_count": 60,
            "eval_count": 30,
        }

        with patch("anvilcv.ai.ollama.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.return_value = mock_response

            result = asyncio.run(provider.generate(request))

        assert result.content == "Local model response"
        assert result.provider == "ollama"

    def test_generate_connection_error(self):
        import httpx

        provider = OllamaProvider(base_url="http://localhost:99999")
        request = _make_request()

        with patch("anvilcv.ai.ollama.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(AnvilAIProviderError, match="Cannot connect"):
                asyncio.run(provider.generate(request))


# --- Token Budget Calculator ---


class TestTokenBudget:
    def test_budget_fits(self):
        from anvilcv.ai.token_budget import calculate_budget

        caps = AnthropicProvider(api_key="test").get_capabilities()
        result = calculate_budget(caps, "Short resume text", "Short job description")
        assert result["resume_tokens"] > 0
        assert result["job_tokens"] > 0
        assert result["total_budget"] == 200_000

    def test_budget_truncates_job(self):
        from anvilcv.ai.token_budget import calculate_budget

        caps = OllamaProvider().get_capabilities()  # Small context (8K)
        long_job = "x" * 50_000  # Way too long for 8K context
        result = calculate_budget(caps, "Short resume", long_job)
        assert result["job_tokens"] < len(long_job) // 4  # Was truncated

    def test_budget_resume_too_large(self):
        from anvilcv.ai.token_budget import calculate_budget

        caps = OllamaProvider().get_capabilities()  # Small context (8K)
        huge_resume = "x" * 100_000  # Way too large
        with pytest.raises(AnvilAIProviderError, match="too large"):
            calculate_budget(caps, huge_resume)


# --- Output Parser ---


class TestOutputParser:
    def test_parse_yaml_from_code_block(self):
        from anvilcv.ai.output_parser import parse_yaml_from_response

        content = "Here's the YAML:\n```yaml\nkey: value\n```"
        assert parse_yaml_from_response(content) == "key: value"

    def test_parse_yaml_raw(self):
        from anvilcv.ai.output_parser import parse_yaml_from_response

        content = "key: value\nother: stuff"
        assert parse_yaml_from_response(content) == "key: value\nother: stuff"

    def test_parse_json_from_code_block(self):
        from anvilcv.ai.output_parser import parse_json_from_response

        content = '```json\n{"key": "value"}\n```'
        result = parse_json_from_response(content)
        assert result == {"key": "value"}

    def test_parse_json_invalid(self):
        from anvilcv.ai.output_parser import parse_json_from_response

        assert parse_json_from_response("not json at all") is None

    def test_generate_with_retry_success(self):
        from anvilcv.ai.output_parser import generate_with_retry
        from anvilcv.ai.provider import GenerationResponse

        async def mock_generate(req):
            return GenerationResponse(
                content="valid output",
                model="test",
                provider="test",
            )

        result = asyncio.run(generate_with_retry(mock_generate, _make_request(), "anthropic"))
        assert result.content == "valid output"

    def test_generate_with_retry_validates(self):
        from anvilcv.ai.output_parser import generate_with_retry
        from anvilcv.ai.provider import GenerationResponse

        call_count = 0

        async def mock_generate(req):
            nonlocal call_count
            call_count += 1
            return GenerationResponse(
                content="invalid" if call_count == 1 else "valid",
                model="test",
                provider="test",
            )

        result = asyncio.run(
            generate_with_retry(
                mock_generate,
                _make_request(),
                "anthropic",
                validate_fn=lambda c: c == "valid",
            )
        )
        assert result.content == "valid"
        assert call_count == 2  # First attempt failed validation, second succeeded
