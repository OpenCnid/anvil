"""Job description model for parsed job postings.

Why:
    Job descriptions drive tailoring, keyword matching, and scoring.
    They're stored as YAML in .anvil/jobs/ for reuse across commands.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pydantic

from anvilcv.vendor.rendercv.schema.models.base import BaseModelWithoutExtraKeys


class JobRequirements(BaseModelWithoutExtraKeys):
    """Parsed requirements from a job description."""

    required_skills: list[str] = pydantic.Field(
        default_factory=list,
        description="Skills explicitly required by the job.",
    )
    preferred_skills: list[str] = pydantic.Field(
        default_factory=list,
        description="Skills listed as preferred or nice-to-have.",
    )
    experience_years: int | None = pydantic.Field(
        default=None,
        ge=0,
        description="Years of experience required.",
    )
    education: str | None = pydantic.Field(
        default=None,
        description="Education requirement (e.g., 'BS Computer Science').",
    )


class JobDescription(BaseModelWithoutExtraKeys):
    """A parsed job description."""

    title: str = pydantic.Field(
        description="Job title.",
    )
    company: str = pydantic.Field(
        description="Company name.",
    )
    url: str | None = pydantic.Field(
        default=None,
        description="URL of the job posting.",
    )
    fetched_at: datetime | None = pydantic.Field(
        default=None,
        description="When the job description was fetched.",
    )
    source: Literal["url", "file", "stdin"] = pydantic.Field(
        default="file",
        description="How the job description was obtained.",
    )
    requirements: JobRequirements = pydantic.Field(
        default_factory=JobRequirements,
        description="Parsed requirements from the job description.",
    )
    raw_text: str = pydantic.Field(
        default="",
        description="Raw text of the job description for AI consumption.",
    )
