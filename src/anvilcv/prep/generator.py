"""Interview prep notes generator.

Why:
    `anvil prep` generates per-project talking points matched to job
    requirements. The output is Markdown with structured sections for
    each experience/project entry.
"""

from __future__ import annotations

import logging
import pathlib

from anvilcv.ai.prompts.interview_prep.common import build_prep_prompt
from anvilcv.ai.provider import AIProvider, GenerationRequest, TaskType
from anvilcv.schema.job_description import JobDescription
from anvilcv.tailoring.matcher import ResumeMatch

logger = logging.getLogger(__name__)


def extract_resume_text(resume_data: dict) -> str:
    """Extract a text representation of the resume for prompting."""
    lines = []
    cv = resume_data.get("cv", resume_data)

    name = cv.get("name", "")
    if name:
        lines.append(f"# {name}")

    sections = cv.get("sections", {})
    for section_name, entries in sections.items():
        lines.append(f"\n## {section_name.replace('_', ' ').title()}")
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict):
                    lines.append(_format_entry(entry))
                elif isinstance(entry, str):
                    lines.append(f"- {entry}")
        elif isinstance(entries, str):
            lines.append(entries)

    return "\n".join(lines)


def _format_entry(entry: dict) -> str:
    """Format a single entry for the prompt."""
    parts = []
    title = entry.get("company") or entry.get("institution") or entry.get("name", "")
    position = entry.get("position") or entry.get("degree", "")
    if title:
        parts.append(f"### {title}")
    if position:
        area = entry.get("area", "")
        if area:
            parts.append(f"{position} in {area}")
        else:
            parts.append(position)

    start = entry.get("start_date", "")
    end = entry.get("end_date", "")
    if start:
        parts.append(f"{start} — {end}" if end else str(start))

    highlights = entry.get("highlights", [])
    for h in highlights:
        parts.append(f"- {h}")

    if entry.get("label"):
        parts.append(f"**{entry['label']}:** {entry.get('details', '')}")

    return "\n".join(parts)


async def generate_prep_notes(
    provider: AIProvider,
    resume_data: dict,
    job: JobDescription,
    match: ResumeMatch,
) -> str:
    """Generate interview preparation notes using AI.

    Args:
        provider: AI provider instance.
        resume_data: Full resume YAML data.
        job: Parsed job description.
        match: Resume-to-job match results.

    Returns:
        Markdown string with interview prep notes.
    """
    resume_text = extract_resume_text(resume_data)
    matched_skills = list(match.resume_skills)
    missing_skills = match.missing_required

    system_prompt, user_prompt = build_prep_prompt(resume_text, job, matched_skills, missing_skills)

    request = GenerationRequest(
        task=TaskType.INTERVIEW_PREP,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.4,
    )

    response = await provider.generate(request)
    return response.content.strip()


def write_prep_notes(
    content: str,
    output_path: pathlib.Path,
) -> pathlib.Path:
    """Write prep notes to a Markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
