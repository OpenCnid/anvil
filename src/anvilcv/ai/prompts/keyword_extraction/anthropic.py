"""Anthropic Claude-optimized prompt for keyword extraction.

Why:
    Claude's large context window (200K) can process full job descriptions
    without truncation. XML tags provide clear structure for extracting
    categorized skills from the response.
"""

from __future__ import annotations


def build_prompt(
    job_text: str,
) -> tuple[str, str]:
    """Build Claude-optimized prompts for keyword extraction.

    Uses XML tags for structured output that's easy to parse.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You extract technical skills, tools, and requirements from job "
        "descriptions. You categorize them as required or preferred based "
        "on the language used (must-have, required, minimum vs. nice-to-have, "
        "preferred, bonus, ideal). Return results in XML tags."
    )

    user_prompt = (
        f"<job_description>\n{job_text}\n</job_description>\n\n"
        f"Extract all technical skills, tools, frameworks, methodologies, "
        f"and certifications from the job description above. Categorize each "
        f"as required or preferred.\n\n"
        f"Return the result in this format:\n"
        f"<required>\n- skill1\n- skill2\n</required>\n"
        f"<preferred>\n- skill1\n- skill2\n</preferred>"
    )

    return system_prompt, user_prompt
