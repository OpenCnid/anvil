"""Common prompt building for AI-enhanced keyword extraction.

Why:
    The heuristic keyword extractor uses a taxonomy for matching, but AI
    can identify skills and requirements that aren't in the taxonomy —
    emerging technologies, domain-specific terms, and implicit requirements.
    This prompt supplements the heuristic pipeline when a provider is available.
"""

from __future__ import annotations


def build_extraction_prompt(
    job_text: str,
) -> tuple[str, str]:
    """Build system and user prompts for keyword extraction.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You extract technical skills, tools, and requirements from job "
        "descriptions. Categorize them as required or preferred. "
        "Return a structured list — no commentary."
    )

    user_prompt = (
        f"Extract all technical skills, tools, frameworks, and requirements "
        f"from this job description. Categorize each as 'required' or "
        f"'preferred' based on context.\n\n"
        f"Job Description:\n{job_text}\n\n"
        f"Return the result as two lists:\n"
        f"REQUIRED:\n- skill1\n- skill2\n\n"
        f"PREFERRED:\n- skill1\n- skill2"
    )

    return system_prompt, user_prompt
