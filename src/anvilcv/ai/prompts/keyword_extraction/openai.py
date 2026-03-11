"""OpenAI GPT-optimized prompt for keyword extraction.

Why:
    GPT-4o supports native JSON mode, making structured output reliable.
    This prompt requests JSON output for clean parsing of categorized skills.
"""

from __future__ import annotations


def build_prompt(
    job_text: str,
) -> tuple[str, str]:
    """Build GPT-optimized prompts for keyword extraction.

    Uses concise instructions optimized for JSON mode output.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You extract technical skills from job descriptions and return them "
        'as JSON with "required" and "preferred" arrays of strings.'
    )

    user_prompt = (
        f"Extract technical skills, tools, and frameworks from this job "
        f"description. Categorize as required or preferred.\n\n"
        f"{job_text}\n\n"
        f'Return JSON: {{"required": ["skill1", ...], "preferred": ["skill1", ...]}}'
    )

    return system_prompt, user_prompt
