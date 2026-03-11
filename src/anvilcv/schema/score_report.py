"""ATS score report model.

Why:
    Score reports capture detailed results from ATS compatibility checks,
    including per-rule pass/fail status, confidence levels, and recommendations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pydantic

from anvilcv.vendor.rendercv.schema.models.base import BaseModelWithoutExtraKeys


class Check(BaseModelWithoutExtraKeys):
    """A single scoring check result."""

    name: str = pydantic.Field(description="Human-readable check name.")
    status: Literal["pass", "fail", "warn"] = pydantic.Field(
        description="Check result.",
    )
    confidence: Literal["evidence_based", "opinionated_heuristic"] = pydantic.Field(
        default="evidence_based",
        description="How confident we are in this check.",
    )
    detail: str | None = pydantic.Field(
        default=None,
        description="Additional detail about the check result.",
    )
    source: str | None = pydantic.Field(
        default=None,
        description="Citation for evidence-based checks.",
    )


class SectionScore(BaseModelWithoutExtraKeys):
    """Score and checks for one scoring section."""

    score: int = pydantic.Field(ge=0, le=100, description="Section score 0-100.")
    checks: list[Check] = pydantic.Field(default_factory=list)


class KeywordMatchSection(BaseModelWithoutExtraKeys):
    """Keyword matching results when scored against a job description."""

    score: int = pydantic.Field(ge=0, le=100)
    job_keywords: list[str] = pydantic.Field(default_factory=list)
    matched: list[str] = pydantic.Field(default_factory=list)
    missing: list[str] = pydantic.Field(default_factory=list)
    partial: list[str] = pydantic.Field(default_factory=list)


class Recommendation(BaseModelWithoutExtraKeys):
    """An actionable recommendation from scoring."""

    priority: Literal["high", "medium", "low"] = pydantic.Field(
        description="Recommendation priority.",
    )
    message: str = pydantic.Field(
        description="Human-readable recommendation.",
    )


class ScoreReport(BaseModelWithoutExtraKeys):
    """Complete ATS score report."""

    file: str = pydantic.Field(description="Path to the scored file.")
    scored_at: datetime = pydantic.Field(default_factory=datetime.now)
    overall_score: int = pydantic.Field(
        ge=0, le=100, description="Overall ATS score 0-100."
    )
    job: str | None = pydantic.Field(
        default=None,
        description="Path to the job description YAML, if scored against one.",
    )
    parsability: SectionScore = pydantic.Field(default_factory=SectionScore)
    structure: SectionScore = pydantic.Field(default_factory=SectionScore)
    keyword_match: KeywordMatchSection | None = pydantic.Field(
        default=None,
        description="Present only when scored against a job description.",
    )
    recommendations: list[Recommendation] = pydantic.Field(default_factory=list)
