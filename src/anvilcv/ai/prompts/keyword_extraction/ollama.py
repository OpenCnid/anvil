"""Ollama-optimized prompt for keyword extraction.

Why:
    Local models have limited context (~8K tokens). This prompt truncates
    the job description to fit and uses a simple list format that smaller
    models can reliably produce.
"""

from __future__ import annotations


def build_prompt(
    job_text: str,
) -> tuple[str, str]:
    """Build simplified prompts for local Ollama models.

    Truncates job text to fit within limited context windows.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = "You list technical skills found in job descriptions."

    # Truncate for small context windows
    truncated = job_text[:3000] if len(job_text) > 3000 else job_text

    user_prompt = (
        f"List the technical skills from this job posting.\n\n"
        f"{truncated}\n\n"
        f"REQUIRED:\n- \n\nPREFERRED:\n- "
    )

    return system_prompt, user_prompt
