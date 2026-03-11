"""Tests for GitHub scanner, cache, metrics, and entry generation.

Why:
    The GitHub scanner makes API calls that must be mocked for unit testing.
    Tests verify: repo data parsing, language computation, cache read/write,
    entry generation with quality scoring, and CLI integration.
"""

import pathlib
from unittest.mock import MagicMock, patch

from anvilcv.github.cache import (
    clear_cache,
    read_cached_profile,
    write_cached_profile,
)
from anvilcv.github.entry_generator import (
    generate_entries,
    generate_project_entry,
    generate_projects_section,
)
from anvilcv.github.metrics import (
    compute_language_percentages,
    compute_repo_quality_score,
    get_primary_language,
    is_recently_active,
)
from anvilcv.github.scanner import GitHubScanner, build_github_repo
from anvilcv.schema.github_profile import (
    GitHubProfile,
    GitHubRepo,
    GitHubSummary,
)

# --- Sample data ---

SAMPLE_REPO_DATA = {
    "name": "awesome-project",
    "description": "A really cool project",
    "html_url": "https://github.com/testuser/awesome-project",
    "stargazers_count": 42,
    "forks_count": 5,
    "language": "Python",
    "topics": ["python", "cli"],
    "created_at": "2024-01-15T00:00:00Z",
    "pushed_at": "2026-03-01T12:00:00Z",
    "default_branch": "main",
    "open_issues_count": 3,
    "fork": False,
    "license": {"spdx_id": "MIT"},
}

SAMPLE_REPO_DATA_2 = {
    "name": "small-lib",
    "description": "A small utility library",
    "html_url": "https://github.com/testuser/small-lib",
    "stargazers_count": 2,
    "forks_count": 0,
    "language": "Go",
    "topics": [],
    "created_at": "2025-06-01T00:00:00Z",
    "pushed_at": "2025-12-15T08:00:00Z",
    "default_branch": "main",
    "open_issues_count": 0,
    "fork": False,
    "license": None,
}


def _make_profile(repos: list[GitHubRepo] | None = None) -> GitHubProfile:
    if repos is None:
        repos = [
            build_github_repo(
                SAMPLE_REPO_DATA,
                languages={"Python": 8000, "Shell": 2000},
                commit_count=150,
                user_commits=120,
                has_tests=True,
                has_ci=True,
            ),
            build_github_repo(
                SAMPLE_REPO_DATA_2,
                languages={"Go": 5000},
                commit_count=20,
                user_commits=20,
            ),
        ]
    return GitHubProfile(
        username="testuser",
        repos=repos,
        summary=GitHubSummary(
            total_repos=len(repos),
            total_stars=sum(r.stars for r in repos),
        ),
    )


# --- Metrics tests ---

class TestMetrics:
    def test_language_percentages(self):
        result = compute_language_percentages({"Python": 8000, "Shell": 2000})
        assert result["Python"] == 80.0
        assert result["Shell"] == 20.0

    def test_language_percentages_empty(self):
        assert compute_language_percentages({}) == {}

    def test_primary_language(self):
        assert get_primary_language({"Python": 8000, "Go": 2000}) == "Python"

    def test_primary_language_empty(self):
        assert get_primary_language({}) is None

    def test_recently_active(self):
        recent = "2026-03-10T12:00:00Z"
        assert is_recently_active(recent, days=90) is True

    def test_not_recently_active(self):
        old = "2020-01-01T00:00:00Z"
        assert is_recently_active(old, days=90) is False

    def test_recently_active_none(self):
        assert is_recently_active(None) is False

    def test_quality_score_high(self):
        score = compute_repo_quality_score(
            stars=100, has_tests=True, has_ci=True,
            has_license=True, user_commits=200,
        )
        assert score > 70

    def test_quality_score_low(self):
        score = compute_repo_quality_score(stars=0, user_commits=1)
        assert score < 20

    def test_quality_score_zero(self):
        score = compute_repo_quality_score()
        assert score == 0


# --- Scanner build_github_repo tests ---

class TestBuildGithubRepo:
    def test_basic_fields(self):
        repo = build_github_repo(SAMPLE_REPO_DATA)
        assert repo.name == "awesome-project"
        assert repo.stars == 42
        assert repo.forks == 5
        assert repo.primary_language == "Python"

    def test_with_languages(self):
        repo = build_github_repo(
            SAMPLE_REPO_DATA,
            languages={"Python": 8000, "Shell": 2000},
        )
        assert repo.languages["Python"] == 80.0
        assert repo.languages["Shell"] == 20.0

    def test_with_metrics(self):
        repo = build_github_repo(
            SAMPLE_REPO_DATA,
            commit_count=150,
            user_commits=120,
            has_tests=True,
            has_ci=True,
        )
        assert repo.metrics.total_commits == 150
        assert repo.metrics.user_commits == 120
        assert repo.metrics.has_tests is True
        assert repo.metrics.has_ci is True

    def test_license_extraction(self):
        repo = build_github_repo(SAMPLE_REPO_DATA)
        assert repo.metrics.license == "MIT"

    def test_no_license(self):
        repo = build_github_repo(SAMPLE_REPO_DATA_2)
        assert repo.metrics.license is None

    def test_topics(self):
        repo = build_github_repo(SAMPLE_REPO_DATA)
        assert "python" in repo.topics
        assert "cli" in repo.topics


# --- Cache tests ---

class TestGitHubCache:
    def test_write_and_read(self, tmp_path: pathlib.Path):
        profile = _make_profile()
        write_cached_profile(profile, base_path=tmp_path)
        cached = read_cached_profile("testuser", base_path=tmp_path)
        assert cached is not None
        assert cached.username == "testuser"
        assert len(cached.repos) == 2

    def test_expired_cache(self, tmp_path: pathlib.Path):
        profile = _make_profile()
        write_cached_profile(profile, base_path=tmp_path)
        # Read with 0 TTL (immediate expiry)
        cached = read_cached_profile("testuser", base_path=tmp_path, ttl_seconds=0)
        assert cached is None

    def test_missing_cache(self, tmp_path: pathlib.Path):
        cached = read_cached_profile("nonexistent", base_path=tmp_path)
        assert cached is None

    def test_clear_user_cache(self, tmp_path: pathlib.Path):
        profile = _make_profile()
        write_cached_profile(profile, base_path=tmp_path)
        clear_cache("testuser", base_path=tmp_path)
        cached = read_cached_profile(
            "testuser", base_path=tmp_path, ttl_seconds=3600
        )
        assert cached is None

    def test_clear_all_cache(self, tmp_path: pathlib.Path):
        profile = _make_profile()
        write_cached_profile(profile, base_path=tmp_path)
        clear_cache(base_path=tmp_path)
        cached = read_cached_profile(
            "testuser", base_path=tmp_path, ttl_seconds=3600
        )
        assert cached is None


# --- Entry generator tests ---

class TestEntryGenerator:
    def test_generate_project_entry(self):
        repo = build_github_repo(
            SAMPLE_REPO_DATA,
            has_ci=True,
            has_tests=True,
        )
        entry = generate_project_entry(repo)
        assert entry["name"] == "awesome-project"
        assert entry["url"] == "https://github.com/testuser/awesome-project"
        assert len(entry["highlights"]) >= 1

    def test_entry_has_metadata_line(self):
        repo = build_github_repo(
            SAMPLE_REPO_DATA,
            has_ci=True,
            has_tests=True,
        )
        entry = generate_project_entry(repo)
        meta = entry["highlights"][-1]
        assert "★ 42" in meta
        assert "Python" in meta

    def test_entry_date(self):
        repo = build_github_repo(SAMPLE_REPO_DATA)
        entry = generate_project_entry(repo)
        assert entry["date"] == "2026-03-01"

    def test_generate_entries_sorted_by_quality(self):
        profile = _make_profile()
        entries = generate_entries(profile)
        assert len(entries) == 2
        # First entry should be the higher quality one (awesome-project)
        assert entries[0]["name"] == "awesome-project"

    def test_generate_entries_max_limit(self):
        profile = _make_profile()
        entries = generate_entries(profile, max_entries=1)
        assert len(entries) == 1

    def test_generate_entries_min_stars_filter(self):
        profile = _make_profile()
        entries = generate_entries(profile, min_stars=10)
        assert len(entries) == 1
        assert entries[0]["name"] == "awesome-project"

    def test_generate_projects_section(self):
        profile = _make_profile()
        section = generate_projects_section(profile)
        assert "projects" in section
        assert len(section["projects"]) == 2


# --- Scanner API tests (mocked) ---

class TestGitHubScannerAPI:
    def test_headers_without_token(self):
        scanner = GitHubScanner()
        headers = scanner._headers()
        assert "Authorization" not in headers

    def test_headers_with_token(self):
        scanner = GitHubScanner(token="ghp_test123")
        headers = scanner._headers()
        assert headers["Authorization"] == "Bearer ghp_test123"

    @patch("anvilcv.github.scanner.httpx.get")
    def test_fetch_repos(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [SAMPLE_REPO_DATA]
        mock_response.headers = {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Limit": "5000",
        }
        mock_get.return_value = mock_response

        scanner = GitHubScanner(token="ghp_test")
        repos, etag = scanner.fetch_repos("testuser", max_repos=10)
        assert len(repos) == 1
        assert repos[0]["name"] == "awesome-project"

    @patch("anvilcv.github.scanner.httpx.get")
    def test_304_not_modified(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 304
        mock_response.headers = {
            "ETag": '"abc123"',
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Limit": "5000",
        }
        mock_get.return_value = mock_response

        scanner = GitHubScanner(token="ghp_test")
        repos, etag = scanner.fetch_repos("testuser", etag='"old_etag"')
        assert repos == []

    @patch("anvilcv.github.scanner.httpx.get")
    def test_rate_limit_tracking(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.headers = {
            "X-RateLimit-Remaining": "10",
            "X-RateLimit-Limit": "5000",
        }
        mock_get.return_value = mock_response

        scanner = GitHubScanner(token="ghp_test")
        scanner.fetch_repos("testuser")
        assert scanner.rate_limit_remaining == 10


# --- CLI tests ---

class TestScanCLI:
    def test_scan_requires_github(self):
        from typer.testing import CliRunner

        import anvilcv.cli.scan_command.scan_command  # noqa: F401
        from anvilcv.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 1
        assert "--github" in result.output or "required" in result.output.lower()

    def test_scan_help(self):
        from typer.testing import CliRunner

        import anvilcv.cli.scan_command.scan_command  # noqa: F401
        from anvilcv.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0
        assert "github" in result.output.lower()
