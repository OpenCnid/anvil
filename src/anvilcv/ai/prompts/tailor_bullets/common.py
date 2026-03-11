"""Common prompt building for bullet tailoring.

Why:
    Bullet tailoring rewrites resume bullet points to better match job
    requirements. The shared prompt logic extracts job data, skills to
    emphasize, and rules that apply across all providers.
"""

from __future__ import annotations

from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch


def build_tailor_prompt(
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
) -> tuple[str, str]:
    """Build system and user prompts for bullet rewriting.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You are a professional resume writer. You rewrite bullet points "
        "to better match job descriptions while maintaining truthfulness. "
        "Return only the rewritten bullet, no explanations."
    )

    missing_skills = ", ".join(match.missing_required[:5])
    required = ", ".join(job.requirements.required_skills[:10])

    user_prompt = (
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

    return system_prompt, user_prompt
