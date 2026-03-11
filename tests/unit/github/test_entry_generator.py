"""Tests for GitHub entry generator.

Why:
    Tests cover edge cases in generate_project_entry, including the
    IndexError/TypeError fallback when parsing last_push date (lines 49-50).
"""

from __future__ import annotations

from anvilcv.github.entry_generator import generate_project_entry
from anvilcv.schema.github_profile import GitHubRepo


class TestGenerateProjectEntryDateParsing:
    """Test date parsing edge cases in generate_project_entry."""

    def test_normal_date(self) -> None:
        repo = GitHubRepo(
            name="my-repo",
            url="https://github.com/user/my-repo",
            last_push="2024-03-15T10:00:00Z",
        )
        entry = generate_project_entry(repo)
        assert entry["date"] == "2024-03-15"

    def test_no_last_push_uses_present(self) -> None:
        repo = GitHubRepo(
            name="my-repo",
            url="https://github.com/user/my-repo",
            last_push=None,
        )
        entry = generate_project_entry(repo)
        assert entry["date"] == "present"

    def test_empty_string_last_push_is_falsy(self) -> None:
        """Empty string is falsy, so last_push branch is skipped."""
        repo = GitHubRepo(
            name="my-repo",
            url="https://github.com/user/my-repo",
            last_push="",
        )
        entry = generate_project_entry(repo)
        assert entry["date"] == "present"

    def test_short_last_push_string(self) -> None:
        """Short string for last_push still works (no IndexError for slicing)."""
        repo = GitHubRepo(
            name="my-repo",
            url="https://github.com/user/my-repo",
            last_push="2024",
        )
        entry = generate_project_entry(repo)
        assert entry["date"] == "2024"

    def test_last_push_type_error_falls_through(self) -> None:
        """Lines 49-50: TypeError when last_push is non-sliceable falls back."""
        from unittest.mock import MagicMock

        # Create a mock repo where last_push is an int (non-sliceable)
        repo = MagicMock()
        repo.name = "my-repo"
        repo.url = "https://github.com/user/my-repo"
        repo.description = None
        repo.stars = 0
        repo.primary_language = None
        repo.metrics.has_ci = False
        repo.metrics.has_tests = False
        repo.last_push = 12345  # int, will cause TypeError on [:10]

        entry = generate_project_entry(repo)
        # TypeError on int[:10] is caught, date_str stays "present"
        assert entry["date"] == "present"

    def test_no_description_uses_name(self) -> None:
        repo = GitHubRepo(
            name="my-repo",
            url="https://github.com/user/my-repo",
        )
        entry = generate_project_entry(repo)
        assert entry["highlights"] == ["my-repo"]

    def test_with_stars_and_language(self) -> None:
        repo = GitHubRepo(
            name="my-repo",
            url="https://github.com/user/my-repo",
            description="A cool project",
            stars=42,
            primary_language="Python",
        )
        entry = generate_project_entry(repo)
        assert len(entry["highlights"]) == 2
        assert "A cool project" in entry["highlights"]
        meta = entry["highlights"][1]
        assert "42" in meta
        assert "Python" in meta
