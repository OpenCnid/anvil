"""OpenAI GPT-optimized prompt for bullet tailoring.

Why:
    GPT-4o works best with concise, direct instructions and supports native
    JSON mode. This prompt uses shorter, structured instructions that align
    with GPT's prompting best practices.
"""

from __future__ import annotations

from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch


def build_prompt(
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
) -> tuple[str, str]:
    """Build GPT-optimized system and user prompts for bullet rewriting.

    Uses concise instructions optimized for GPT models.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You rewrite resume bullet points to match job descriptions. "
        "Preserve facts, metrics, and truthfulness. Use strong action verbs. "
        "Return only the rewritten bullet — no explanation, no formatting."
    )

    required = ", ".join(job.requirements.required_skills[:10])
    missing = ", ".join(match.missing_required[:5])

    user_prompt = (
        f"Job: {job.title} at {job.company}\n"
        f"Required: {required}\n"
        f"Emphasize: {missing}\n\n"
        f"Original: {bullet}\n\n"
        f"Rewrite the bullet to align with the job. Keep 1-2 lines. "
        f"Don't fabricate skills or experience."
    )

    return system_prompt, user_prompt
