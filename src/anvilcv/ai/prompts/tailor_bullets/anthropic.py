"""Anthropic Claude-optimized prompt for bullet tailoring.

Why:
    Claude excels with XML-structured prompts and has a 200K context window.
    This prompt uses XML tags for clear input delineation and output extraction,
    leveraging Claude's strong instruction-following with structured formats.
"""

from __future__ import annotations

from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch


def build_prompt(
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
) -> tuple[str, str]:
    """Build Claude-optimized system and user prompts for bullet rewriting.

    Uses XML tags for structured input/output per Claude best practices.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You are a resume optimization assistant. You rewrite resume bullet "
        "points to better match a target job description while preserving "
        "factual accuracy.\n\n"
        "Rules:\n"
        "- Never fabricate achievements, metrics, or technologies not present "
        "in the original\n"
        "- Rewrite for keyword alignment and emphasis, not invention\n"
        "- Preserve specific numbers and metrics exactly\n"
        "- Use strong action verbs (built, led, designed, shipped, optimized)\n"
        "- Keep the bullet to 1-2 lines maximum\n"
        "- Return ONLY the rewritten bullet inside <rewritten> tags"
    )

    required = ", ".join(job.requirements.required_skills[:10])
    preferred = ", ".join(job.requirements.preferred_skills[:5])
    missing = ", ".join(match.missing_required[:5])

    user_prompt = (
        f"<job>\n"
        f"<title>{job.title}</title>\n"
        f"<company>{job.company}</company>\n"
        f"<required_skills>{required}</required_skills>\n"
        f"<preferred_skills>{preferred}</preferred_skills>\n"
        f"</job>\n\n"
        f"<skills_to_emphasize>{missing}</skills_to_emphasize>\n\n"
        f"<original_bullet>{bullet}</original_bullet>\n\n"
        f"Rewrite the bullet to emphasize skills matching the job requirements. "
        f"Return the result inside <rewritten> tags.\n\n"
        f"<rewritten>"
    )

    return system_prompt, user_prompt
