"""Common prompt building for interview prep generation.

Why:
    Interview prep generates per-project talking points matched to job
    requirements. The prompt needs resume data, job requirements, and
    matched skills to produce structured Markdown output.
"""

from __future__ import annotations

from anvilcv.schema.job_description import JobDescription


def build_prep_prompt(
    resume_text: str,
    job: JobDescription,
    matched_skills: list[str],
    missing_skills: list[str],
) -> tuple[str, str]:
    """Build system and user prompts for interview prep generation.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You are an expert interview coach. Given a resume and job description, "
        "generate structured talking points for each project and experience entry. "
        "Format: 'If they ask about X, lead with Y from project Z.' "
        "Be specific — reference actual projects, metrics, and skills from the resume. "
        "Output in Markdown format with headers for each section."
    )

    required = ", ".join(job.requirements.required_skills[:10])
    preferred = ", ".join(job.requirements.preferred_skills[:5])
    matched = ", ".join(matched_skills[:10])
    missing = ", ".join(missing_skills[:5])

    user_prompt = (
        f"# Interview Preparation\n\n"
        f"## Job\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Required skills: {required}\n"
        f"Preferred skills: {preferred}\n\n"
        f"## Skills Analysis\n"
        f"Your matched skills: {matched}\n"
        f"Skills to address: {missing}\n\n"
        f"## Resume\n"
        f"{resume_text}\n\n"
        f"## Instructions\n"
        f"Generate interview preparation notes with:\n"
        f"1. A section for each experience/project entry in the resume\n"
        f"2. Key talking points that connect the entry to job requirements\n"
        f"3. Specific metrics and achievements to highlight\n"
        f"4. How to address missing skills using related experience\n"
        f"5. Sample behavioral questions they might ask about each entry\n\n"
        f"Format as Markdown with ## headers for each entry."
    )

    return system_prompt, user_prompt
