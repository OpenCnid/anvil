"""Token budget calculator for AI requests.

Why:
    Each AI provider has a finite context window. We need to fit the system
    prompt, resume content, job description, few-shot examples, and output
    reserve into that window. When content exceeds the budget, we truncate
    the job description first (it's less critical than the resume itself).
    If the resume alone exceeds the budget, we raise an explicit error.

    Per spec: "Prefer truncating job description over resume. Raise error
    if resume too large for context window."
"""

import logging

from anvilcv.ai.provider import ProviderCapabilities
from anvilcv.exceptions import AnvilAIProviderError

logger = logging.getLogger(__name__)

# Rough token estimation: ~4 chars per token for English text.
# This is a heuristic; actual tokenization varies by model.
CHARS_PER_TOKEN = 4

# Fixed overhead for system prompt structure, XML tags, instructions
SYSTEM_OVERHEAD_TOKENS = 500

# Reserve for few-shot examples in prompts
FEW_SHOT_RESERVE_TOKENS = 1000


def estimate_tokens(text: str) -> int:
    """Estimate token count from text length. Conservative (overestimates)."""
    return len(text) // CHARS_PER_TOKEN + 1


def calculate_budget(
    capabilities: ProviderCapabilities,
    resume_text: str,
    job_text: str | None = None,
    output_reserve: int | None = None,
) -> dict[str, int | str]:
    """Calculate token budget and truncate job description if needed.

    Returns:
        Dictionary with:
        - resume_tokens: estimated tokens for resume
        - job_tokens: estimated tokens for (possibly truncated) job description
        - job_text: the (possibly truncated) job description text
        - available_tokens: tokens available for user content
        - output_reserve: tokens reserved for model output
        - total_budget: total context window
    """
    total = capabilities.max_context_tokens
    output = output_reserve or capabilities.max_output_tokens
    overhead = SYSTEM_OVERHEAD_TOKENS + FEW_SHOT_RESERVE_TOKENS

    available = total - output - overhead
    if available <= 0:
        raise AnvilAIProviderError(
            message=(
                f"Context window ({total} tokens) is too small after reserving "
                f"{output} for output and {overhead} for system overhead."
            )
        )

    resume_tokens = estimate_tokens(resume_text)

    if resume_tokens > available:
        raise AnvilAIProviderError(
            message=(
                f"Resume is too large ({resume_tokens} estimated tokens) for this "
                f"model's context window ({total} tokens, {available} available after "
                f"overhead). Try a model with a larger context window."
            )
        )

    remaining = available - resume_tokens
    truncated_job = job_text or ""
    job_tokens = 0

    if job_text:
        job_tokens = estimate_tokens(job_text)
        if job_tokens > remaining:
            # Truncate job description to fit
            max_chars = remaining * CHARS_PER_TOKEN
            truncated_job = job_text[:max_chars]
            job_tokens = remaining
            logger.warning(
                "Job description truncated from %d to %d estimated tokens to fit context window.",
                estimate_tokens(job_text),
                job_tokens,
            )

    return {
        "resume_tokens": resume_tokens,
        "job_tokens": job_tokens,
        "job_text": truncated_job,
        "available_tokens": available,
        "output_reserve": output,
        "total_budget": total,
    }
