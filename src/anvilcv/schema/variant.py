"""Variant provenance model for tracking tailored resume variants.

Why:
    Each tailored variant needs provenance metadata so users know what
    was changed, by which AI, against which job description, and when.
"""

from __future__ import annotations

from datetime import datetime

import pydantic

from anvilcv.vendor.rendercv.schema.models.base import BaseModelWithoutExtraKeys


class VariantChange(BaseModelWithoutExtraKeys):
    """A single change made during tailoring."""

    section: str = pydantic.Field(
        description="YAML path of the changed section (e.g., 'experience.0.highlights').",
    )
    action: str = pydantic.Field(
        description="Type of change: 'rewritten', 'reordered', 'added', 'removed'.",
    )
    detail: str = pydantic.Field(
        default="",
        description="Human-readable description of the change.",
    )


class VariantMetadata(BaseModelWithoutExtraKeys):
    """Provenance metadata for a tailored variant."""

    source: str = pydantic.Field(
        description="Path to the source YAML file.",
    )
    job: str | None = pydantic.Field(
        default=None,
        description="Path to the job description YAML.",
    )
    created_at: datetime = pydantic.Field(
        default_factory=datetime.now,
        description="When this variant was created.",
    )
    provider: str = pydantic.Field(
        description="AI provider that generated this variant.",
    )
    model: str = pydantic.Field(
        description="AI model that generated this variant.",
    )
    changes: list[VariantChange] = pydantic.Field(
        default_factory=list,
        description="List of changes made during tailoring.",
    )
