"""Tests for ``anvil scan`` CLI command.

Why:
    The scan command fetches GitHub repos and generates project entries.
    Tests cover --github flag, output formats (yaml/json/entries-only),
    caching, --merge, error cases, and missing GITHUB_TOKEN warning.
"""

from __future__ import annotations

import json
import pathlib
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

import anvilcv.cli.scan_command.scan_command  # noqa: F401
from anvilcv.cli.app import app
from anvilcv.schema.github_profile import (
    GitHubProfile,
    GitHubRepo,
    GitHubSummary,
)

runner = CliRunner()


def _make_profile(username: str = "testuser", num_repos: int = 2) -> GitHubProfile:
    """Build a minimal GitHubProfile for testing."""
    repos = [
        GitHubRepo(
            name=f"repo-{i}",
            url=f"https://github.com/{username}/repo-{i}",
            stars=10 * i,
            primary_language="Python",
        )
        for i in range(1, num_repos + 1)
    ]
    return GitHubProfile(
        username=username,
        repos=repos,
        summary=GitHubSummary(
            total_repos=num_repos,
            total_stars=sum(r.stars for r in repos),
            primary_languages=["Python"],
        ),
    )


class TestScanRequiresGithub:
    """--github is required."""

    def test_no_github_flag_exits_1(self) -> None:
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 1
        assert "--github" in result.output.lower() or "required" in result.output.lower()


class TestScanCachedData:
    """When cached data exists and --force-refresh is not set, use cache."""

    @patch("anvilcv.github.cache.write_cached_profile")
    @patch("anvilcv.github.cache.read_cached_profile")
    def test_uses_cache(
        self,
        mock_read_cache: MagicMock,
        mock_write_cache: MagicMock,
    ) -> None:
        """Cached profile is used without re-fetching."""
        profile = _make_profile()
        mock_read_cache.return_value = profile

        result = runner.invoke(app, ["scan", "--github", "testuser"])
        assert result.exit_code == 0
        assert "Using cached data" in result.output
        assert "Found 2 repos" in result.output
        mock_write_cache.assert_not_called()


class TestScanFreshFetch:
    """When no cache exists, fetch from GitHub."""

    @patch("anvilcv.github.cache.write_cached_profile")
    @patch("anvilcv.github.scanner.scan_user")
    @patch("anvilcv.github.cache.read_cached_profile")
    def test_fetches_fresh(
        self,
        mock_read_cache: MagicMock,
        mock_scan: MagicMock,
        mock_write_cache: MagicMock,
    ) -> None:
        """Fresh scan when cache is empty."""
        mock_read_cache.return_value = None
        profile = _make_profile()
        mock_scan.return_value = profile

        with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_fake123"}):
            result = runner.invoke(app, ["scan", "--github", "testuser"])

        assert result.exit_code == 0
        assert "Scanning GitHub repos" in result.output
        mock_write_cache.assert_called_once_with(profile)

    @patch("anvilcv.github.cache.write_cached_profile")
    @patch("anvilcv.github.scanner.scan_user")
    @patch("anvilcv.github.cache.read_cached_profile")
    def test_no_github_token_warning(
        self,
        mock_read_cache: MagicMock,
        mock_scan: MagicMock,
        mock_write_cache: MagicMock,
    ) -> None:
        """Missing GITHUB_TOKEN prints a rate limit warning."""
        mock_read_cache.return_value = None
        mock_scan.return_value = _make_profile()

        with patch.dict("os.environ", {}, clear=True):
            result = runner.invoke(app, ["scan", "--github", "testuser"])

        assert result.exit_code == 0
        assert "GITHUB_TOKEN" in result.output or "rate limit" in result.output.lower()


class TestScanForceRefresh:
    """--force-refresh skips cache."""

    @patch("anvilcv.github.cache.write_cached_profile")
    @patch("anvilcv.github.scanner.scan_user")
    @patch("anvilcv.github.cache.read_cached_profile")
    def test_force_refresh_skips_cache(
        self,
        mock_read_cache: MagicMock,
        mock_scan: MagicMock,
        mock_write_cache: MagicMock,
    ) -> None:
        profile = _make_profile()
        mock_scan.return_value = profile

        with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_fake"}):
            result = runner.invoke(app, ["scan", "--github", "testuser", "--force-refresh"])

        assert result.exit_code == 0
        mock_read_cache.assert_not_called()
        mock_scan.assert_called_once()


class TestScanOutputFormats:
    """Test --format yaml, json, entries-only."""

    @patch("anvilcv.github.cache.read_cached_profile")
    def test_json_format_stdout(self, mock_read_cache: MagicMock) -> None:
        mock_read_cache.return_value = _make_profile()

        result = runner.invoke(app, ["scan", "--github", "testuser", "--format", "json"])
        assert result.exit_code == 0
        # The output should contain JSON data
        assert '"username"' in result.output or "testuser" in result.output

    @patch("anvilcv.github.cache.read_cached_profile")
    def test_json_format_to_file(self, mock_read_cache: MagicMock, tmp_path: pathlib.Path) -> None:
        mock_read_cache.return_value = _make_profile()
        out = tmp_path / "profile.json"

        result = runner.invoke(
            app,
            ["scan", "--github", "testuser", "--format", "json", "--output", str(out)],
        )
        assert result.exit_code == 0
        data = json.loads(out.read_text())
        assert data["username"] == "testuser"

    @patch("anvilcv.github.cache.read_cached_profile")
    def test_yaml_format_to_file(self, mock_read_cache: MagicMock, tmp_path: pathlib.Path) -> None:
        mock_read_cache.return_value = _make_profile()
        out = tmp_path / "profile.yaml"

        result = runner.invoke(
            app,
            ["scan", "--github", "testuser", "--format", "yaml", "--output", str(out)],
        )
        assert result.exit_code == 0
        assert out.exists()
        assert "Profile written to" in result.output

    @patch("anvilcv.github.entry_generator.generate_entries")
    @patch("anvilcv.github.cache.read_cached_profile")
    def test_entries_only_format(
        self,
        mock_read_cache: MagicMock,
        mock_gen: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        mock_read_cache.return_value = _make_profile()
        mock_gen.return_value = [{"name": "repo-1", "highlights": ["Built thing"]}]
        out = tmp_path / "entries.yaml"

        result = runner.invoke(
            app,
            [
                "scan",
                "--github",
                "testuser",
                "--format",
                "entries-only",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        assert "Entries written to" in result.output


class TestScanNoRepos:
    """No repos found prints a message and exits 0."""

    @patch("anvilcv.github.cache.read_cached_profile")
    def test_no_repos(self, mock_read_cache: MagicMock) -> None:
        profile = GitHubProfile(
            username="emptyuser",
            repos=[],
            summary=GitHubSummary(),
        )
        mock_read_cache.return_value = profile

        result = runner.invoke(app, ["scan", "--github", "emptyuser"])
        assert result.exit_code == 0
        assert "No public repositories found" in result.output


class TestScanErrors:
    """Error cases."""

    @patch("anvilcv.github.scanner.scan_user")
    @patch("anvilcv.github.cache.read_cached_profile")
    def test_scan_api_error_exits_3(
        self,
        mock_read_cache: MagicMock,
        mock_scan: MagicMock,
    ) -> None:
        """GitHub API errors exit with code 3."""
        mock_read_cache.return_value = None
        mock_scan.side_effect = RuntimeError("API rate limited")

        with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_fake"}):
            result = runner.invoke(app, ["scan", "--github", "testuser"])

        assert result.exit_code == 3
        assert "Error scanning GitHub" in result.output


class TestScanMerge:
    """--merge merges entries into existing YAML."""

    @patch("anvilcv.github.entry_generator.generate_entries")
    @patch("anvilcv.github.cache.read_cached_profile")
    def test_merge_into_yaml(
        self,
        mock_read_cache: MagicMock,
        mock_gen: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        mock_read_cache.return_value = _make_profile()
        mock_gen.return_value = [{"name": "repo-1"}]

        yaml_file = tmp_path / "resume.yaml"
        yaml_file.write_text("cv:\n  name: Test\n  sections:\n    skills: []\n")

        result = runner.invoke(
            app,
            ["scan", "--github", "testuser", "--merge", str(yaml_file)],
        )
        assert result.exit_code == 0
        assert "Merged" in result.output
