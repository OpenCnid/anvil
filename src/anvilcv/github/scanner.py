"""GitHub API client for repository scanning.

Why:
    `anvil scan --github <user>` fetches repo metadata via the GitHub REST API.
    Uses conditional requests (ETag/If-None-Match) to minimize API calls on
    re-scans. Respects rate limits and warns when approaching threshold.
"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from anvilcv.schema.github_profile import GitHubProfile, GitHubRepo, RepoMetrics

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
RATE_LIMIT_WARN_THRESHOLD = 0.10  # Warn at 10% remaining


class GitHubScanner:
    """Fetches repository data from GitHub REST API."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = GITHUB_API_BASE,
    ):
        self.token = token
        self.base_url = base_url
        self._rate_limit_remaining: int | None = None
        self._rate_limit_total: int | None = None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _update_rate_limit(self, response: httpx.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        limit = response.headers.get("X-RateLimit-Limit")
        if remaining is not None:
            self._rate_limit_remaining = int(remaining)
        if limit is not None:
            self._rate_limit_total = int(limit)

        if (
            self._rate_limit_remaining is not None
            and self._rate_limit_total is not None
            and self._rate_limit_total > 0
        ):
            ratio = self._rate_limit_remaining / self._rate_limit_total
            if ratio <= RATE_LIMIT_WARN_THRESHOLD:
                logger.warning(
                    "GitHub API rate limit low: %d/%d remaining",
                    self._rate_limit_remaining,
                    self._rate_limit_total,
                )

    def _get(
        self,
        path: str,
        params: dict | None = None,
        etag: str | None = None,
    ) -> tuple[httpx.Response | None, str | None]:
        """Make a GET request with optional conditional request support.

        Returns:
            (response, new_etag) — response is None if 304 Not Modified.
        """
        headers = self._headers()
        if etag:
            headers["If-None-Match"] = etag

        url = f"{self.base_url}{path}"
        response = httpx.get(url, headers=headers, params=params, timeout=30)
        self._update_rate_limit(response)

        new_etag = response.headers.get("ETag")

        if response.status_code == 304:
            return None, new_etag

        response.raise_for_status()
        return response, new_etag

    def fetch_repos(
        self,
        username: str,
        max_repos: int = 100,
        since: str | None = None,
        etag: str | None = None,
    ) -> tuple[list[dict], str | None]:
        """Fetch public repositories for a user.

        Args:
            username: GitHub username.
            max_repos: Maximum repos to return.
            since: ISO date string — only repos pushed after this date.
            etag: ETag from previous request for conditional fetch.

        Returns:
            (repos_data, new_etag) — repos_data is empty list if 304.
        """
        all_repos: list[dict] = []
        page = 1
        per_page = min(max_repos, 100)
        current_etag = etag

        while len(all_repos) < max_repos:
            response, current_etag = self._get(
                f"/users/{username}/repos",
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": "pushed",
                    "type": "owner",
                },
                etag=etag if page == 1 else None,
            )

            if response is None:
                # 304 Not Modified
                return [], current_etag

            repos = response.json()
            if not repos:
                break

            all_repos.extend(repos)
            page += 1

            if len(repos) < per_page:
                break

        # Filter by since date
        if since:
            all_repos = [
                r for r in all_repos
                if r.get("pushed_at", "") >= since
            ]

        return all_repos[:max_repos], current_etag

    def fetch_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Fetch language breakdown for a repository."""
        try:
            response, _ = self._get(f"/repos/{owner}/{repo}/languages")
            if response is None:
                return {}
            result: dict[str, int] = response.json()
            return result
        except httpx.HTTPStatusError:
            return {}

    def fetch_commit_count(
        self,
        owner: str,
        repo: str,
        author: str | None = None,
    ) -> int:
        """Fetch approximate commit count for a repo."""
        try:
            params: dict[str, str | int] = {"per_page": 1}
            if author:
                params["author"] = author
            response, _ = self._get(
                f"/repos/{owner}/{repo}/commits",
                params=params,
            )
            if response is None:
                return 0
            # Parse Link header for last page number
            link = response.headers.get("Link", "")
            if 'rel="last"' in link:
                import re
                match = re.search(r'page=(\d+)>; rel="last"', link)
                if match:
                    return int(match.group(1))
            return len(response.json())
        except httpx.HTTPStatusError:
            return 0

    def check_file_exists(self, owner: str, repo: str, path: str) -> bool:
        """Check if a file/directory exists in a repo."""
        try:
            response, _ = self._get(f"/repos/{owner}/{repo}/contents/{path}")
            return response is not None
        except httpx.HTTPStatusError:
            return False

    @property
    def rate_limit_remaining(self) -> int | None:
        return self._rate_limit_remaining


def build_github_repo(
    repo_data: dict,
    languages: dict[str, int] | None = None,
    commit_count: int = 0,
    user_commits: int = 0,
    has_tests: bool = False,
    has_ci: bool = False,
) -> GitHubRepo:
    """Convert raw GitHub API response to GitHubRepo model."""
    # Compute language percentages
    lang_pct: dict[str, float] = {}
    if languages:
        total = sum(languages.values())
        if total > 0:
            lang_pct = {
                lang: round(bytes_count / total * 100, 1)
                for lang, bytes_count in languages.items()
            }

    license_info = repo_data.get("license")
    license_name = license_info.get("spdx_id") if license_info else None

    return GitHubRepo(
        name=repo_data["name"],
        description=repo_data.get("description"),
        url=repo_data.get("html_url", ""),
        stars=repo_data.get("stargazers_count", 0),
        forks=repo_data.get("forks_count", 0),
        primary_language=repo_data.get("language"),
        languages=lang_pct,
        topics=repo_data.get("topics", []),
        created_at=repo_data.get("created_at"),
        last_push=repo_data.get("pushed_at"),
        default_branch=repo_data.get("default_branch", "main"),
        metrics=RepoMetrics(
            total_commits=commit_count,
            user_commits=user_commits,
            open_issues=repo_data.get("open_issues_count", 0),
            has_tests=has_tests,
            has_ci=has_ci,
            license=license_name,
        ),
    )


def scan_user(
    username: str,
    token: str | None = None,
    max_repos: int = 100,
    since: str | None = None,
    include_metrics: bool = True,
) -> GitHubProfile:
    """Scan a GitHub user's public repositories.

    Args:
        username: GitHub username.
        token: GitHub personal access token (optional but recommended).
        max_repos: Maximum repos to scan.
        since: Only repos pushed after this ISO date.
        include_metrics: If True, fetch languages and commit counts per repo.

    Returns:
        GitHubProfile with all scanned data.
    """
    scanner = GitHubScanner(token=token)
    repos_data, _ = scanner.fetch_repos(username, max_repos=max_repos, since=since)

    repos: list[GitHubRepo] = []
    for repo_data in repos_data:
        if repo_data.get("fork"):
            continue

        languages = {}
        commit_count = 0
        user_commits = 0
        has_tests = False
        has_ci = False

        if include_metrics:
            repo_name = repo_data["name"]
            languages = scanner.fetch_languages(username, repo_name)
            commit_count = scanner.fetch_commit_count(username, repo_name)
            user_commits = scanner.fetch_commit_count(
                username, repo_name, author=username
            )
            has_ci = scanner.check_file_exists(
                username, repo_name, ".github/workflows"
            )
            has_tests = scanner.check_file_exists(
                username, repo_name, "tests"
            ) or scanner.check_file_exists(
                username, repo_name, "test"
            )

        repos.append(
            build_github_repo(
                repo_data,
                languages=languages,
                commit_count=commit_count,
                user_commits=user_commits,
                has_tests=has_tests,
                has_ci=has_ci,
            )
        )

    # Build summary
    from anvilcv.schema.github_profile import GitHubSummary

    total_stars = sum(r.stars for r in repos)
    total_commits = sum(r.metrics.total_commits for r in repos)

    # Primary languages by usage across repos
    lang_counts: dict[str, int] = {}
    for repo in repos:
        if repo.primary_language:
            lang_counts[repo.primary_language] = (
                lang_counts.get(repo.primary_language, 0) + 1
            )
    primary_langs = sorted(lang_counts, key=lambda x: lang_counts[x], reverse=True)[:5]

    # Active repos (pushed in last 90 days)
    now = datetime.now()
    active_count = 0
    for repo in repos:
        if repo.last_push:
            try:
                push_dt = datetime.fromisoformat(
                    repo.last_push.replace("Z", "+00:00")
                )
                if (now - push_dt.replace(tzinfo=None)).days <= 90:
                    active_count += 1
            except ValueError:
                pass

    return GitHubProfile(
        username=username,
        rate_limit_remaining=scanner.rate_limit_remaining,
        repos=repos,
        summary=GitHubSummary(
            total_repos=len(repos),
            total_stars=total_stars,
            primary_languages=primary_langs,
            total_commits=total_commits,
            active_repos_last_90_days=active_count,
        ),
    )
