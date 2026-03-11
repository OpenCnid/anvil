"""AI bullet rewriting for resume tailoring.

Why:
    The rewriter takes matched resume bullets and rewrites them using
    AI to better align with job requirements. It uses the provider
    interface from F-ANV-09 and per-provider prompts per design
    principle P5 (providers are pluggable not fungible).
"""

from __future__ import annotations

import logging
import re

from anvilcv.ai.prompts.selector import get_prompt_builder
from anvilcv.ai.prompts.tailor_bullets.common import build_tailor_prompt
from anvilcv.ai.provider import AIProvider, GenerationRequest, TaskType
from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch

logger = logging.getLogger(__name__)


def build_rewrite_prompt(
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
    provider_name: str = "",
) -> tuple[str, str]:
    """Build a prompt for rewriting a single bullet point.

    Uses per-provider prompts when available (Anthropic XML, OpenAI concise,
    Ollama simplified), falling back to the common prompt.
    """
    # Try per-provider prompt first
    if provider_name:
        builder = get_prompt_builder("tailor_bullets", provider_name)
        if builder is not None:
            try:
                result: tuple[str, str] = builder(bullet, job, match)
                return result
            except TypeError:
                logger.debug("Per-provider prompt builder signature mismatch, using common")

    # Fall back to common prompt
    return build_tailor_prompt(bullet, job, match)


def _extract_rewritten_bullet(content: str) -> str:
    """Extract the rewritten bullet from provider response.

    Handles XML-tagged output from Anthropic (<rewritten>...</rewritten>)
    and plain text from other providers.
    """
    # Try XML tag extraction (Anthropic)
    xml_match = re.search(r"<rewritten>(.*?)</rewritten>", content, re.DOTALL)
    if xml_match:
        return xml_match.group(1).strip()

    # Plain text — strip quotes, dashes, "Rewritten:" prefix
    result = content.strip()
    result = re.sub(r"^(?:Rewritten:\s*)", "", result, flags=re.IGNORECASE)
    result = result.strip("\"'- ")
    return result


async def rewrite_bullet(
    provider: AIProvider,
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
) -> str:
    """Rewrite a single bullet point using AI.

    Returns the rewritten bullet or the original if rewriting fails.
    """
    system_prompt, user_prompt = build_rewrite_prompt(
        bullet, job, match, provider_name=provider.name
    )

    request = GenerationRequest(
        task=TaskType.TAILOR_BULLETS,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )

    try:
        response = await provider.generate(request)
        rewritten = _extract_rewritten_bullet(response.content)
        # Basic validation: should be similar length, not empty
        if rewritten and len(rewritten) < len(bullet) * 5:
            return rewritten
        logger.warning("Rewritten bullet was too long or empty, using original")
        return bullet
    except Exception as e:
        logger.warning("Failed to rewrite bullet: %s", e)
        return bullet


async def rewrite_top_bullets(
    provider: AIProvider,
    bullets: list[tuple[str, str]],  # (section_path, content)
    job: JobDescription,
    match: ResumeMatch,
    max_rewrites: int = 10,
) -> dict[str, str]:
    """Rewrite the top N most relevant bullets.

    Returns a mapping of section_path → rewritten content.
    """
    results: dict[str, str] = {}

    for section_path, content in bullets[:max_rewrites]:
        rewritten = await rewrite_bullet(provider, content, job, match)
        if rewritten != content:
            results[section_path] = rewritten

    return results
