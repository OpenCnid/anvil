"""Match resume content to job requirements.

Why:
    Before AI rewriting, we identify which resume sections, bullets, and
    projects are most relevant to the job description. This matching
    informs what gets prioritized, rewritten, or reordered.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from anvilcv.schema.job_description import JobDescription
from anvilcv.scoring.keyword_extractor import extract_skills


@dataclass
class MatchResult:
    """Result of matching a resume section to job requirements."""

    section_path: str  # e.g., "experience.0.highlights.2"
    content: str
    matched_skills: list[str] = field(default_factory=list)
    relevance_score: float = 0.0  # 0.0 to 1.0


@dataclass
class ResumeMatch:
    """Complete matching result for a resume against a job."""

    matches: list[MatchResult] = field(default_factory=list)
    resume_skills: list[str] = field(default_factory=list)
    job_required_skills: list[str] = field(default_factory=list)
    job_preferred_skills: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)


def match_resume_to_job(
    resume_data: dict,
    job: JobDescription,
) -> ResumeMatch:
    """Match resume content against a job description.

    Extracts skills from each resume section and computes relevance
    scores against the job's requirements.
    """
    cv = resume_data.get("cv", {})
    sections = cv.get("sections", {})

    required = set(s.lower() for s in job.requirements.required_skills)
    preferred = set(s.lower() for s in job.requirements.preferred_skills)
    all_job_skills = required | preferred

    matches: list[MatchResult] = []
    all_resume_skills: set[str] = set()

    for section_name, entries in sections.items():
        if not isinstance(entries, list):
            continue

        for i, entry in enumerate(entries):
            # Extract highlights/bullets
            highlights = entry.get("highlights", []) if isinstance(entry, dict) else []
            for j, bullet in enumerate(highlights):
                if not isinstance(bullet, str):
                    continue

                bullet_skills = extract_skills(bullet)
                all_resume_skills.update(s.lower() for s in bullet_skills)

                matched = [
                    s for s in bullet_skills if s.lower() in all_job_skills
                ]
                relevance = (
                    len(matched) / len(all_job_skills)
                    if all_job_skills
                    else 0.0
                )

                matches.append(
                    MatchResult(
                        section_path=f"{section_name}.{i}.highlights.{j}",
                        content=bullet,
                        matched_skills=matched,
                        relevance_score=relevance,
                    )
                )

    # Sort by relevance (most relevant first)
    matches.sort(key=lambda m: m.relevance_score, reverse=True)

    resume_skills_list = list(
        extract_skills(
            " ".join(
                str(v)
                for v in _flatten_values(cv)
            )
        )
    )
    resume_lower = {s.lower() for s in resume_skills_list}

    return ResumeMatch(
        matches=matches,
        resume_skills=resume_skills_list,
        job_required_skills=job.requirements.required_skills,
        job_preferred_skills=job.requirements.preferred_skills,
        missing_required=[
            s for s in job.requirements.required_skills
            if s.lower() not in resume_lower
        ],
        missing_preferred=[
            s for s in job.requirements.preferred_skills
            if s.lower() not in resume_lower
        ],
    )


def _flatten_values(d: dict | list | str) -> list[str]:
    """Recursively flatten all string values from a nested structure."""
    if isinstance(d, str):
        return [d]
    if isinstance(d, list):
        result = []
        for item in d:
            result.extend(_flatten_values(item))
        return result
    if isinstance(d, dict):
        result = []
        for v in d.values():
            result.extend(_flatten_values(v))
        return result
    return [str(d)] if d is not None else []
