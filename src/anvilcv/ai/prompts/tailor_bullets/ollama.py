"""Ollama-optimized prompt for bullet tailoring.

Why:
    Local models (llama3.1:8b) have small context windows (~8K tokens) and
    may struggle with complex instructions. This prompt is simplified:
    shorter, fewer constraints, single clear instruction. Includes one
    example for format clarity since smaller models benefit from examples.
"""

from __future__ import annotations

from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch


def build_prompt(
    bullet: str,
    job: JobDescription,
    match: ResumeMatch,
) -> tuple[str, str]:
    """Build simplified prompts for local Ollama models.

    Shorter prompts to fit within limited context windows. Includes one
    example for format clarity.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = "You rewrite resume bullets to match job descriptions. Be concise."

    required = ", ".join(job.requirements.required_skills[:5])

    user_prompt = (
        f"Job: {job.title} at {job.company}\n"
        f"Key skills: {required}\n\n"
        f"Example:\n"
        f"Original: Managed cloud infrastructure for web applications\n"
        f"Rewritten: Managed AWS cloud infrastructure for 12 production web "
        f"applications using Terraform and Kubernetes\n\n"
        f"Now rewrite this bullet:\n"
        f"Original: {bullet}\n"
        f"Rewritten:"
    )

    return system_prompt, user_prompt
