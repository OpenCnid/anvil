"""GitHub profile model for scan results.

Why:
    GitHub scan results are stored as structured data for use in
    tailoring (project selection) and entry generation.
"""

from __future__ import annotations

from datetime import datetime

import pydantic

from anvilcv.vendor.rendercv.schema.models.base import BaseModelWithoutExtraKeys


class RepoMetrics(BaseModelWithoutExtraKeys):
    """Detailed metrics for a GitHub repository."""

    total_commits: int = pydantic.Field(default=0)
    user_commits: int = pydantic.Field(default=0)
    open_issues: int = pydantic.Field(default=0)
    contributors: int = pydantic.Field(default=0)
    has_tests: bool = pydantic.Field(default=False)
    has_ci: bool = pydantic.Field(default=False)
    license: str | None = pydantic.Field(default=None)


class GitHubRepo(BaseModelWithoutExtraKeys):
    """A single GitHub repository from scan results."""

    name: str = pydantic.Field(description="Repository name.")
    description: str | None = pydantic.Field(default=None)
    url: str = pydantic.Field(description="Repository URL.")
    stars: int = pydantic.Field(default=0)
    forks: int = pydantic.Field(default=0)
    primary_language: str | None = pydantic.Field(default=None)
    languages: dict[str, float] = pydantic.Field(
        default_factory=dict,
        description="Language breakdown by percentage.",
    )
    topics: list[str] = pydantic.Field(default_factory=list)
    created_at: str | None = pydantic.Field(default=None)
    last_push: str | None = pydantic.Field(default=None)
    default_branch: str = pydantic.Field(default="main")
    metrics: RepoMetrics = pydantic.Field(default_factory=RepoMetrics)


class GitHubSummary(BaseModelWithoutExtraKeys):
    """Aggregated statistics across all scanned repos."""

    total_repos: int = pydantic.Field(default=0)
    total_stars: int = pydantic.Field(default=0)
    primary_languages: list[str] = pydantic.Field(default_factory=list)
    total_commits: int = pydantic.Field(default=0)
    active_repos_last_90_days: int = pydantic.Field(default=0)


class GitHubProfile(BaseModelWithoutExtraKeys):
    """Complete GitHub scan results."""

    username: str = pydantic.Field(description="GitHub username.")
    scanned_at: datetime = pydantic.Field(default_factory=datetime.now)
    rate_limit_remaining: int | None = pydantic.Field(default=None)
    repos: list[GitHubRepo] = pydantic.Field(default_factory=list)
    summary: GitHubSummary = pydantic.Field(default_factory=GitHubSummary)
