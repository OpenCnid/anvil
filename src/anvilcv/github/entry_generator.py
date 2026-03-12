"""Convert GitHub repository data to rendercv YAML entries.

Why:
    `anvil scan --github <user> --merge INPUT` generates resume-ready project
    entries from GitHub data. Each entry uses the NormalEntry format with a
    metadata line showing stars, language, and last update.
"""

from __future__ import annotations

from anvilcv.github.metrics import compute_repo_quality_score, is_recently_active
from anvilcv.schema.github_profile import GitHubProfile, GitHubRepo


def generate_project_entry(repo: GitHubRepo) -> dict:
    """Convert a GitHubRepo to a rendercv NormalEntry dict.

    Format:
        name: repo-name
        date: last_push date
        highlights:
          - Description
          - ★ stars · primary_language · Quality signals
    """
    highlights = []

    if repo.description:
        highlights.append(repo.description)

    # Metadata line: ★ stars · language · signals
    meta_parts = []
    if repo.stars > 0:
        meta_parts.append(f"★ {repo.stars}")
    if repo.primary_language:
        meta_parts.append(repo.primary_language)
    if repo.metrics.has_ci:
        meta_parts.append("CI/CD")
    if repo.metrics.has_tests:
        meta_parts.append("Tests")

    if meta_parts:
        highlights.append(" · ".join(meta_parts))

    # Format date from ISO timestamp
    date_str = "present"
    if repo.last_push:
        try:
            date_str = repo.last_push[:10]  # YYYY-MM-DD
        except (IndexError, TypeError):
            pass

    entry = {
        "name": repo.name,
        "date": date_str,
        "url": repo.url,
        "highlights": highlights or [repo.name],
    }

    return entry


def generate_entries(
    profile: GitHubProfile,
    max_entries: int = 10,
    min_stars: int = 0,
    min_commits: int = 0,
    only_active: bool = False,
) -> list[dict]:
    """Generate project entries from a GitHub profile, sorted by quality.

    Args:
        profile: Scanned GitHub profile.
        max_entries: Maximum entries to generate.
        min_stars: Minimum stars filter.
        min_commits: Minimum user commits filter.
        only_active: If True, only include repos active in last 90 days.

    Returns:
        List of rendercv NormalEntry dicts.
    """
    repos = profile.repos

    # Apply filters
    if min_stars > 0:
        repos = [r for r in repos if r.stars >= min_stars]
    if min_commits > 0:
        repos = [r for r in repos if r.metrics.user_commits >= min_commits]
    if only_active:
        repos = [r for r in repos if is_recently_active(r.last_push)]

    # Score and sort by quality
    scored = [
        (
            repo,
            compute_repo_quality_score(
                stars=repo.stars,
                has_tests=repo.metrics.has_tests,
                has_ci=repo.metrics.has_ci,
                has_license=repo.metrics.license is not None,
                user_commits=repo.metrics.user_commits,
            ),
        )
        for repo in repos
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [generate_project_entry(repo) for repo, _ in scored[:max_entries]]


def generate_projects_section(
    profile: GitHubProfile,
    **kwargs,
) -> dict:
    """Generate a complete projects section for merging into resume YAML.

    Returns a dict ready to be inserted as cv.sections.projects.
    """
    entries = generate_entries(profile, **kwargs)
    return {"projects": entries}
