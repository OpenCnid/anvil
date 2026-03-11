"""Tests for unified job description input resolver.

Why:
    The CLI spec requires `--job PATH_OR_URL_OR_STDIN` across score, tailor,
    cover, and prep commands. This module tests URL, file, and stdin routing.
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pytest

from anvilcv.cli.job_input import (
    _basic_html_to_text,
    _looks_like_spa,
    resolve_job_input,
)
from anvilcv.exceptions import AnvilServiceError, AnvilUserError


class TestResolveJobInput:
    """Test input routing for file, URL, and stdin."""

    def test_file_path(self, tmp_path: pathlib.Path) -> None:
        """Local file path routes to parse_job_from_file."""
        job_file = tmp_path / "job.txt"
        job_file.write_text("Senior Python Engineer at TechCo\nRequires Python and AWS")

        result = resolve_job_input(str(job_file))
        assert result.raw_text is not None
        assert "Python" in result.raw_text

    def test_yaml_file_path(self, tmp_path: pathlib.Path) -> None:
        """YAML file routes to parse_job_from_file with YAML parsing."""
        job_file = tmp_path / "job.yaml"
        job_file.write_text(
            "title: Senior Engineer\ncompany: TechCo\n"
            "requirements:\n  required_skills:\n    - python\n    - aws\n"
        )

        result = resolve_job_input(str(job_file))
        assert result.title == "Senior Engineer"
        assert result.company == "TechCo"

    def test_file_not_found(self) -> None:
        """Non-existent file raises AnvilUserError."""
        with pytest.raises(AnvilUserError, match="not found"):
            resolve_job_input("/nonexistent/job.txt")

    @patch("anvilcv.cli.job_input._parse_job_from_url")
    def test_url_routes_to_url_parser(self, mock_url: MagicMock) -> None:
        """HTTP/HTTPS URLs route to URL fetcher."""
        mock_url.return_value = MagicMock()

        resolve_job_input("https://acme.com/careers/sre")
        mock_url.assert_called_once_with("https://acme.com/careers/sre")

    @patch("anvilcv.cli.job_input._parse_job_from_url")
    def test_http_url(self, mock_url: MagicMock) -> None:
        """HTTP URL routes correctly."""
        mock_url.return_value = MagicMock()

        resolve_job_input("http://example.com/jobs/123")
        mock_url.assert_called_once()

    @patch("anvilcv.tailoring.job_parser.parse_job_from_stdin")
    def test_stdin_dash(self, mock_stdin: MagicMock) -> None:
        """'-' routes to stdin parser."""
        mock_stdin.return_value = MagicMock()

        resolve_job_input("-")
        mock_stdin.assert_called_once()


class TestParseJobFromUrl:
    """Test URL fetching and content extraction."""

    @patch("httpx.get")
    def test_successful_fetch(self, mock_get: MagicMock) -> None:
        """Successful URL fetch extracts text and creates JobDescription."""
        from anvilcv.cli.job_input import _parse_job_from_url

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = """
        <html><body>
        <h1>Senior Python Engineer</h1>
        <p>We need someone with Python, AWS, and Kubernetes experience.</p>
        </body></html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _parse_job_from_url("https://acme.com/careers/sre")
        assert result.url == "https://acme.com/careers/sre"
        assert result.source == "url"

    @patch("httpx.get")
    def test_http_error(self, mock_get: MagicMock) -> None:
        """HTTP errors raise AnvilServiceError."""
        import httpx

        from anvilcv.cli.job_input import _parse_job_from_url

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with pytest.raises(AnvilServiceError, match="Could not fetch"):
            _parse_job_from_url("https://acme.com/careers/nonexistent")

    @patch("httpx.get")
    def test_non_html_content_type(self, mock_get: MagicMock) -> None:
        """Non-HTML content type raises AnvilServiceError."""
        from anvilcv.cli.job_input import _parse_job_from_url

        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(AnvilServiceError, match="Expected HTML"):
            _parse_job_from_url("https://acme.com/careers/sre.pdf")

    @patch("httpx.get")
    def test_network_error(self, mock_get: MagicMock) -> None:
        """Network errors raise AnvilServiceError."""
        import httpx

        from anvilcv.cli.job_input import _parse_job_from_url

        mock_get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(AnvilServiceError, match="Could not fetch"):
            _parse_job_from_url("https://unreachable.example.com/job")


class TestSpaDetection:
    """Test SPA/JS-heavy page detection heuristics."""

    def test_spa_with_react_root(self) -> None:
        html = '<html><body><div id="root"></div>'
        html += '<script src="app.js"></script></body></html>'
        assert _looks_like_spa(html)

    def test_spa_with_next_data(self) -> None:
        assert _looks_like_spa("<html><script>window.__NEXT_DATA__={}</script></html>")

    def test_normal_html(self) -> None:
        html = """
        <html><body>
        <h1>Job Posting</h1>
        <p>We are looking for a senior engineer with experience in Python.</p>
        <p>Requirements: 5+ years experience, AWS, Docker</p>
        </body></html>
        """
        assert not _looks_like_spa(html)


class TestBasicHtmlToText:
    """Test fallback HTML-to-text extraction."""

    def test_strips_tags(self) -> None:
        html = "<p>Hello <b>world</b></p>"
        text = _basic_html_to_text(html)
        assert "Hello" in text
        assert "world" in text
        assert "<p>" not in text

    def test_skips_script_and_style(self) -> None:
        html = "<p>Visible</p><script>var x = 1;</script><style>.x{}</style><p>Also visible</p>"
        text = _basic_html_to_text(html)
        assert "Visible" in text
        assert "Also visible" in text
        assert "var x" not in text
