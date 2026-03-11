"""AI bullet rewriting for resume tailoring.

Why:
    The rewriter takes matched resume bullets and rewrites them using
    AI to better align with job requirements. It uses the provider
    interface from F-ANV-09 and per-provider prompts.
"""

from __future__ import annotations

import logging

from anvilcv.ai.provider import AIProvider, GenerationRequest, TaskType
from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch

logger = logging.getLogger(__name__)


def build_rewrite_prompt(
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
) -> str:
    """Build a prompt for rewriting a single bullet point.

    The prompt includes the original bullet, job requirements,
    and skills to emphasize.
    """
    missing_skills = ", ".join(match.missing_required[:5])
    required = ", ".join(job.requirements.required_skills[:10])

    return (
        f"Rewrite this resume bullet point to better match the job requirements.\n"
        f"\n"
        f"Original bullet: {bullet}\n"
        f"\n"
        f"Job title: {job.title} at {job.company}\n"
        f"Required skills: {required}\n"
        f"Skills to emphasize if relevant: {missing_skills}\n"
        f"\n"
        f"Rules:\n"
        f"- Keep the same general meaning and truthfulness\n"
        f"- Use strong action verbs (built, led, designed, shipped)\n"
        f"- Include metrics where the original has them\n"
        f"- Naturally incorporate relevant skills from the job requirements\n"
        f"- Keep it to 1-2 lines maximum\n"
        f"- Do NOT fabricate experience or skills not implied by the original\n"
        f"\n"
        f"Return ONLY the rewritten bullet point, nothing else."
    )


async def rewrite_bullet(
    provider: AIProvider,
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
) -> str:
    """Rewrite a single bullet point using AI.

    Returns the rewritten bullet or the original if rewriting fails.
    """
    prompt = build_rewrite_prompt(bullet, job, match)

    request = GenerationRequest(
        task=TaskType.TAILOR_BULLETS,
        system_prompt=(
            "You are a professional resume writer. You rewrite bullet points "
            "to better match job descriptions while maintaining truthfulness. "
            "Return only the rewritten bullet, no explanations."
        ),
        user_prompt=prompt,
        temperature=0.3,
    )

    try:
        response = await provider.generate(request)
        rewritten = response.content.strip()
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
