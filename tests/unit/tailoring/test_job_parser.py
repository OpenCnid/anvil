"""Tests for job_parser.py — cover uncovered error/edge paths.

Why:
    The job parser handles multi-source input (file, stdin, text).
    These tests cover edge cases: long titles, YAML errors, stdin,
    and non-dict YAML — all paths that were previously uncovered.
"""

from __future__ import annotations

import io
from unittest.mock import patch

import pytest

from anvilcv.exceptions import AnvilUserError
from anvilcv.tailoring.job_parser import (
    parse_job_from_file,
    parse_job_from_stdin,
    parse_job_from_text,
)


class TestParseJobFromText:
    def test_long_title_truncated(self):
        """Line 63-64: Titles > 100 chars default to 'Unknown Position'."""
        long_line = "A" * 150
        text = f"{long_line}\nAcme Corp\nWe need Python skills."
        job = parse_job_from_text(text)
        assert job.title == "Unknown Position"
        assert job.company == "Acme Corp"

    def test_long_company_truncated(self):
        """Line 65-66: Company > 100 chars defaults to 'Unknown Company'."""
        long_company = "B" * 150
        text = f"SRE Engineer\n{long_company}\nWe need Kubernetes."
        job = parse_job_from_text(text)
        assert job.title == "SRE Engineer"
        assert job.company == "Unknown Company"

    def test_empty_text(self):
        """Empty text uses defaults for title and company."""
        job = parse_job_from_text("")
        assert job.title == "Unknown Position"
        assert job.company == "Unknown Company"

    def test_single_line_text(self):
        """Only one line — company defaults."""
        job = parse_job_from_text("Senior Backend Engineer")
        assert job.title == "Senior Backend Engineer"
        assert job.company == "Unknown Company"


class TestParseJobFromStdin:
    def test_stdin_tty_raises(self):
        """Line 46-47: TTY stdin raises user error."""
        with patch("sys.stdin", new_callable=lambda: lambda: io.StringIO("")):
            mock_stdin = io.StringIO("")
            mock_stdin.isatty = lambda: True  # type: ignore[assignment]
            with patch("anvilcv.tailoring.job_parser.sys.stdin", mock_stdin):
                with pytest.raises(AnvilUserError, match="No job description on stdin"):
                    parse_job_from_stdin()

    def test_stdin_reads_text(self):
        """Line 48-49: Non-TTY stdin reads and parses."""
        mock_stdin = io.StringIO("ML Engineer\nAcme AI\nPython, TensorFlow required.")
        mock_stdin.isatty = lambda: False  # type: ignore[assignment]
        with patch("anvilcv.tailoring.job_parser.sys.stdin", mock_stdin):
            job = parse_job_from_stdin()
        assert job.title == "ML Engineer"
        assert job.source == "stdin"


class TestParseYamlJob:
    def test_invalid_yaml(self, tmp_path):
        """Line 87-88: Invalid YAML raises AnvilUserError."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("title: [unclosed bracket", encoding="utf-8")
        with pytest.raises(AnvilUserError, match="Invalid YAML"):
            parse_job_from_file(bad_yaml)

    def test_non_dict_yaml(self, tmp_path):
        """Line 90-91: YAML that parses to non-dict raises AnvilUserError."""
        list_yaml = tmp_path / "list.yaml"
        list_yaml.write_text("- item1\n- item2", encoding="utf-8")
        with pytest.raises(AnvilUserError, match="must be a mapping"):
            parse_job_from_file(list_yaml)
