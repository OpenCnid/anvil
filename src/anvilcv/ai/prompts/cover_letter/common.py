"""Common prompt building for cover letter generation.

Why:
    Cover letters must reference actual projects and skills from the resume,
    not be generic. The prompt needs resume data, job requirements, and
    matched skills to produce a targeted, non-generic cover letter.
"""

from __future__ import annotations

from anvilcv.schema.job_description import JobDescription


def build_cover_letter_prompt(
    resume_text: str,
    job: JobDescription,
    matched_skills: list[str],
    missing_skills: list[str],
) -> tuple[str, str]:
    """Build system and user prompts for cover letter generation.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = (
        "You are a professional cover letter writer. Write a compelling, "
        "specific cover letter that references actual projects, metrics, and "
        "achievements from the candidate's resume. Never be generic — every "
        "paragraph should connect specific experience to the job requirements. "
        "Output in Markdown format. Keep it to 3-4 paragraphs."
    )

    required = ", ".join(job.requirements.required_skills[:10])
    preferred = ", ".join(job.requirements.preferred_skills[:5])
    matched = ", ".join(matched_skills[:10])

    user_prompt = (
        f"# Cover Letter Generation\n\n"
        f"## Job\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Required skills: {required}\n"
        f"Preferred skills: {preferred}\n\n"
        f"## Candidate's Matched Skills\n"
        f"{matched}\n\n"
        f"## Candidate's Resume\n"
        f"{resume_text}\n\n"
        f"## Instructions\n"
        f"Write a cover letter that:\n"
        f"1. Opens with enthusiasm for the specific role at {job.company}\n"
        f"2. Highlights 2-3 specific projects/achievements that match "
        f"the job requirements\n"
        f"3. Uses concrete metrics from the resume (numbers, percentages)\n"
        f"4. Shows awareness of the company and role\n"
        f"5. Closes with a call to action\n\n"
        f"Do NOT fabricate experience. Only reference what's in the resume.\n"
        f"Output the cover letter in Markdown format."
    )

    return system_prompt, user_prompt
