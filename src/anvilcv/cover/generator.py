"""Cover letter generator.

Why:
    `anvil cover` generates a targeted cover letter that references actual
    projects and metrics from the candidate's resume. The output is Markdown,
    non-generic, and connected to job requirements.
"""

from __future__ import annotations

import logging
import pathlib

from anvilcv.ai.prompts.cover_letter.common import build_cover_letter_prompt
from anvilcv.ai.provider import AIProvider, GenerationRequest, TaskType
from anvilcv.prep.generator import extract_resume_text
from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch

logger = logging.getLogger(__name__)


async def generate_cover_letter(
    provider: AIProvider,
    resume_data: dict,
    job: JobDescription,
    match: ResumeMatch,
) -> str:
    """Generate a cover letter using AI.

    Args:
        provider: AI provider instance.
        resume_data: Full resume YAML data.
        job: Parsed job description.
        match: Resume-to-job match results.

    Returns:
        Markdown string with the cover letter.
    """
    resume_text = extract_resume_text(resume_data)
    matched_skills = list(match.resume_skills)
    missing_skills = match.missing_required

    system_prompt, user_prompt = build_cover_letter_prompt(
        resume_text, job, matched_skills, missing_skills
    )

    request = GenerationRequest(
        task=TaskType.COVER_LETTER,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.5,
    )

    response = await provider.generate(request)
    return response.content.strip()


def write_cover_letter(
    content: str,
    output_path: pathlib.Path,
) -> pathlib.Path:
    """Write cover letter to a Markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
