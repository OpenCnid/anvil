"""Metric extraction from GitHub repository data.

Why:
    Raw GitHub API responses contain much more data than we need. This module
    extracts and computes the metrics relevant for resume entries: languages,
    activity, quality signals (tests, CI), and contribution statistics.
"""

from __future__ import annotations

from datetime import datetime


def compute_language_percentages(languages: dict[str, int]) -> dict[str, float]:
    """Convert byte counts to percentages."""
    total = sum(languages.values())
    if total == 0:
        return {}
    return {
        lang: round(bytes_count / total * 100, 1)
        for lang, bytes_count in languages.items()
    }


def get_primary_language(languages: dict[str, int]) -> str | None:
    """Get the language with the most bytes."""
    if not languages:
        return None
    return max(languages, key=languages.get)  # type: ignore[arg-type]


def is_recently_active(pushed_at: str | None, days: int = 90) -> bool:
    """Check if a repo was pushed to within the given number of days."""
    if not pushed_at:
        return False
    try:
        push_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        delta = datetime.now() - push_dt.replace(tzinfo=None)
        return delta.days <= days
    except ValueError:
        return False


def compute_repo_quality_score(
    stars: int = 0,
    has_tests: bool = False,
    has_ci: bool = False,
    has_license: bool = False,
    user_commits: int = 0,
) -> float:
    """Compute a quality score (0-100) for ranking repos in resume entries.

    Scoring:
    - Stars: up to 30 points (log scale)
    - Tests: 20 points
    - CI: 15 points
    - License: 10 points
    - User commits: up to 25 points (log scale)
    """
    import math

    score = 0.0

    # Stars (log scale, max 30)
    if stars > 0:
        score += min(30, math.log10(stars + 1) * 15)

    # Quality signals
    if has_tests:
        score += 20
    if has_ci:
        score += 15
    if has_license:
        score += 10

    # User commits (log scale, max 25)
    if user_commits > 0:
        score += min(25, math.log10(user_commits + 1) * 12)

    return round(score, 1)
