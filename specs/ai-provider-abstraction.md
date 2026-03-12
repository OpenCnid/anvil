# AI Provider Abstraction

## Design Goals

1. Providers are **pluggable** but NOT **interchangeable** (Principle P5)
2. Each provider has a documented capability contract
3. Prompts are per-provider, not one-size-fits-all
4. Failures are explicit and actionable, never silent

## Provider Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class ProviderCapabilities:
    """What this provider can do — queried before making requests."""
    max_context_tokens: int          # Total context window
    max_output_tokens: int           # Maximum output per request
    supports_json_mode: bool         # Native JSON output mode
    supports_structured_output: bool # Schema-constrained output
    supports_system_prompt: bool     # Separate system message role
    rate_limit_rpm: int | None       # Requests per minute (None = unknown)
    rate_limit_tpm: int | None       # Tokens per minute (None = unknown)

@dataclass
class GenerationRequest:
    """What to generate."""
    task: str                        # Task identifier (e.g., "tailor_bullets", "cover_letter")
    system_prompt: str               # System instructions
    user_prompt: str                 # User-facing prompt with content
    output_schema: dict | None       # JSON Schema for structured output (if supported)
    max_output_tokens: int           # Requested max output
    temperature: float = 0.3        # Lower = more deterministic

@dataclass
class GenerationResponse:
    """What came back."""
    content: str                     # Raw text response
    parsed: dict | None             # Parsed structured output (if requested)
    input_tokens: int                # Tokens used for input
    output_tokens: int               # Tokens used for output
    model: str                       # Actual model used
    provider: str                    # Provider name
    latency_ms: int                  # Request latency

class AIProvider(ABC):
    """Abstract base for all AI providers."""

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Return this provider's capability contract."""
        ...

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text or structured output."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this provider's credentials are set."""
        ...

    @abstractmethod
    def get_setup_instructions(self) -> str:
        """Return human-readable setup instructions for this provider."""
        ...
```

## Per-Provider Contracts

### Anthropic Claude (v1 — Tested, Supported)

| Property | Value |
|----------|-------|
| Models | claude-sonnet-4-20250514 (default), claude-opus-4-20250514, claude-haiku-3-20240307 |
| Max context | 200,000 tokens |
| Max output | 8,192 tokens (Sonnet/Opus), 4,096 (Haiku) |
| JSON mode | Not native. Uses XML-tagged output with `<json>` wrapper in prompt |
| Structured output | Via prompted XML structure + post-parse validation |
| System prompt | Supported (separate `system` parameter) |
| Rate limits | Tier-dependent. Tier 1: 50 RPM, 40K TPM. Tier 4: 4000 RPM, 400K TPM |
| Auth | `ANTHROPIC_API_KEY` environment variable |
| Prompting notes | Prefers XML-structured prompts. Best results with explicit output format instructions. Longer context window makes it ideal for processing full resumes + long job descriptions. |

### OpenAI GPT (v1 — Tested, Supported)

| Property | Value |
|----------|-------|
| Models | gpt-4o (default), gpt-4o-mini, gpt-4-turbo |
| Max context | 128,000 tokens (GPT-4o), 128,000 (4o-mini), 128,000 (4-turbo) |
| Max output | 16,384 tokens (GPT-4o), 16,384 (4o-mini) |
| JSON mode | Native (`response_format: {"type": "json_object"}`) |
| Structured output | Native JSON mode + `response_format: {"type": "json_schema", "json_schema": ...}` |
| System prompt | Supported (system role message) |
| Rate limits | Tier-dependent. Tier 1: 500 RPM, 30K TPM. Tier 5: 10K RPM, 12M TPM |
| Auth | `OPENAI_API_KEY` environment variable |
| Prompting notes | Best structured output support via native JSON mode. Use JSON mode for all structured requests. Shorter prompts work better than verbose XML-style instructions. |

### Ollama Local (v1 — Tested, Best-Effort)

| Property | Value |
|----------|-------|
| Models | llama3.1:8b (default), llama3.1:70b — **tested set**. All other Ollama models (mistral, codellama, phi-3, etc.) are accepted but classified as community-contributed/best-effort. |
| Max context | 8,192 tokens (8B default), varies by model and configuration |
| Max output | Context-dependent, typically 2,048-4,096 tokens |
| JSON mode | Partial. Some models support `format: "json"` in Ollama API |
| Structured output | Unreliable. Must validate and retry. |
| System prompt | Supported |
| Rate limits | Local — no external rate limits. Bounded by hardware throughput |
| Auth | No auth required. Base URL: `http://localhost:11434` (default) |
| Prompting notes | Smaller context window limits resume + job description size. For 8B models, truncate job description to key requirements. Structured output may need multiple retries. Output quality varies significantly between models. |

**Ollama best-effort policy:** Ollama support is tested with `llama3.1:8b` and `llama3.1:70b`. Other models are community-contributed and may not produce usable output. Anvil will log a warning when using an untested model: "Model '{model}' has not been tested with Anvil. Output quality may vary."

## Prompt Architecture

### Prompt Registry

Prompts are stored per-task and per-provider in `src/anvilcv/ai/prompts/`:

```
prompts/
├── tailor_bullets/
│   ├── anthropic.py    # Claude-optimized prompt with XML structure
│   ├── openai.py       # GPT-optimized prompt with JSON mode
│   └── ollama.py       # Simplified prompt for smaller models
├── cover_letter/
│   ├── anthropic.py
│   ├── openai.py
│   └── ollama.py
├── interview_prep/
│   ├── anthropic.py
│   ├── openai.py
│   └── ollama.py
└── keyword_extraction/
    ├── anthropic.py
    ├── openai.py
    └── ollama.py
```

### Prompt Structure (Example: Bullet Tailoring)

Each prompt file exports a function that builds the prompt from structured data:

```python
# prompts/tailor_bullets/anthropic.py

def build_prompt(
    resume_section: dict,
    job_requirements: dict,
    job_title: str,
    company: str,
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for Anthropic Claude."""

    system_prompt = """You are a resume optimization assistant. You rewrite resume bullets to better match a target job description while preserving factual accuracy.

Rules:
- Never fabricate achievements, metrics, or technologies not present in the original
- Rewrite for keyword alignment and emphasis, not invention
- Preserve specific numbers and metrics exactly
- Output valid YAML matching the input structure"""

    user_prompt = f"""<job>
<title>{job_title}</title>
<company>{company}</company>
<requirements>
{yaml.dump(job_requirements)}
</requirements>
</job>

<resume_section>
{yaml.dump(resume_section)}
</resume_section>

Rewrite the resume bullets to emphasize skills matching the job requirements. Return the result as a YAML list of strings inside <output> tags.

<output>
"""
    return system_prompt, user_prompt
```

### Prompt Design Differences by Provider

| Aspect | Anthropic | OpenAI | Ollama |
|--------|-----------|--------|--------|
| Output format instruction | XML tags (`<output>...</output>`) | JSON mode with schema | Simple markdown with ```yaml fences |
| Context utilization | Full resume + full JD (fits in 200K) | Full resume + full JD (fits in 128K) | Truncated JD (requirements only) to fit 8K |
| Few-shot examples | 2-3 examples in system prompt | 1-2 examples in system prompt | 1 example (context budget) |
| Retry strategy | 1 retry on parse failure | 1 retry on parse failure | 3 retries on parse failure (higher failure rate) |

## Token Budget Management

Each AI task has a token budget calculator:

```python
def calculate_budget(
    capabilities: ProviderCapabilities,
    resume_tokens: int,
    job_description_tokens: int,
    task: str,
) -> TokenBudget:
    """Calculate token allocation for a task.

    Returns a budget that fits within the provider's context window,
    or raises InsufficientContextError if it can't fit.
    """
    # Reserve tokens for: system prompt + few-shot examples + output
    system_overhead = TASK_OVERHEAD[task]  # Pre-calculated per task
    output_reserve = min(capabilities.max_output_tokens, TASK_MAX_OUTPUT[task])

    available = capabilities.max_context_tokens - system_overhead - output_reserve

    if resume_tokens + job_description_tokens <= available:
        return TokenBudget(resume=resume_tokens, job=job_description_tokens, output=output_reserve)

    # Must truncate — prefer truncating JD over resume
    if resume_tokens > available * 0.6:
        # Resume too large even at 60% budget — error
        raise InsufficientContextError(
            f"Resume is too large ({resume_tokens} tokens) for {capabilities.max_context_tokens} "
            f"context window. Consider shortening your resume or using a provider with a larger context window."
        )

    job_budget = available - resume_tokens
    return TokenBudget(resume=resume_tokens, job=job_budget, output=output_reserve, job_truncated=True)
```

## Fallback Behavior

### No Provider Configured

When a command that requires an AI provider is invoked without one configured:

```
$ anvil tailor resume.yaml --job https://example.com/job

Error: No AI provider configured.

To use AI features, configure a provider in your YAML:

  anvil:
    providers:
      default: anthropic
      anthropic:
        api_key_env: ANTHROPIC_API_KEY

Or pass --provider on the command line:

  anvil tailor resume.yaml --job https://example.com/job --provider anthropic

Supported providers: anthropic, openai, ollama
Docs: https://docs.anvilcv.com/providers
```

### API Down / Network Failure

```
$ anvil tailor resume.yaml --job https://example.com/job --provider anthropic

Error: Could not reach Anthropic API.

Details: ConnectionError — api.anthropic.com:443 — Connection timed out
This is likely a temporary issue with the provider.

Try:
  1. Check your internet connection
  2. Try again in a few minutes
  3. Use a different provider: --provider openai
```

### Malformed Response

```
$ anvil tailor resume.yaml --job https://example.com/job --provider ollama

Warning: AI response could not be parsed as valid YAML (attempt 1/3). Retrying...
Warning: AI response could not be parsed as valid YAML (attempt 2/3). Retrying...
Warning: AI response could not be parsed as valid YAML (attempt 3/3).

Error: AI provider returned unparseable output after 3 attempts.

The raw response has been saved to .anvil/debug/tailor_2026-03-10_150000.txt
This can happen with smaller models. Try:
  1. A larger model: --model llama3.1:70b
  2. A different provider: --provider anthropic
```

## Adding a New Provider

To add a new provider:

1. Create `src/anvilcv/ai/{provider_name}.py` implementing `AIProvider`
2. Add prompts in `src/anvilcv/ai/prompts/{task}/{provider_name}.py` for each task
3. Register the provider in `src/anvilcv/ai/registry.py`
4. Add per-provider Tier 2 golden-set tests
5. Document the provider's capability contract in this spec
6. Add the provider to CLI `--provider` choices and config schema

Minimum capability requirements for a new provider:
- Context window ≥ 4,096 tokens
- Ability to follow structured output instructions (even if not native JSON mode)
- System prompt or equivalent instruction mechanism
