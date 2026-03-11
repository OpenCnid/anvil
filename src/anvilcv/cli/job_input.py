"""Unified job description input resolver for CLI commands.

Why:
    The CLI spec requires `--job PATH_OR_URL_OR_STDIN` across score, tailor,
    cover, and prep commands. This module routes string input to the appropriate
    parser: URL fetching (via httpx + readability-lxml), local file, or stdin.
"""

from __future__ import annotations

import logging
import pathlib
import re

from anvilcv.exceptions import AnvilServiceError, AnvilUserError
from anvilcv.schema.job_description import JobDescription

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


def resolve_job_input(job_arg: str) -> JobDescription:
    """Resolve a --job argument to a JobDescription.

    Handles three input types:
    - "-" → read from stdin
    - URL (http:// or https://) → fetch and extract text via readability-lxml
    - file path → parse local file
    """
    from anvilcv.tailoring.job_parser import (
        parse_job_from_file,
        parse_job_from_stdin,
    )

    if job_arg == "-":
        return parse_job_from_stdin()

    if _URL_PATTERN.match(job_arg):
        return _parse_job_from_url(job_arg)

    path = pathlib.Path(job_arg)
    if not path.exists():
        raise AnvilUserError(message=f"Job description file not found: {job_arg}")
    return parse_job_from_file(path)


def _parse_job_from_url(url: str) -> JobDescription:
    """Fetch a job description from a URL using httpx + readability-lxml.

    Best-effort extraction: warns on SPA-heavy pages that may need JS rendering.
    """
    import httpx

    from anvilcv.tailoring.job_parser import parse_job_from_text

    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "AnvilCV/1.0 (resume tool)"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise AnvilServiceError(
            message=(
                f"Could not fetch job description from {url}: "
                f"HTTP {e.response.status_code}. "
                "Save the job description as a text file "
                "and use `--job ./path/to/job.txt` instead."
            )
        ) from e
    except httpx.RequestError as e:
        raise AnvilServiceError(
            message=(
                f"Could not fetch job description from {url}: {e}. "
                f"Check the URL and your network connection."
            )
        ) from e

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        raise AnvilServiceError(
            message=(
                f"Could not parse job description from {url}. "
                f"Expected HTML, got {content_type}. "
                "Save the job description as a text file "
                "and use `--job ./path/to/job.txt` instead."
            )
        )

    html = response.text

    # Check for SPA indicators
    if _looks_like_spa(html):
        logger.warning(
            "Page at %s may require JavaScript rendering. "
            "Extracted content may be incomplete. "
            "If results look wrong, save the job description text to a file: "
            "`--job ./path/to/job.txt`",
            url,
        )

    # Extract readable text using readability-lxml
    text = _extract_readable_text(html, url)

    if not text.strip():
        raise AnvilServiceError(
            message=(
                f"Could not extract text from {url}. "
                f"The page may require JavaScript. "
                "Save the job description as a text file "
                "and use `--job ./path/to/job.txt` instead."
            )
        )

    job = parse_job_from_text(text, source="url")
    job.url = url
    return job


def _extract_readable_text(html: str, url: str) -> str:
    """Extract readable text from HTML using readability-lxml."""
    try:
        from lxml.html import document_fromstring  # type: ignore[import-untyped]
        from readability import Document  # type: ignore[import-untyped]

        doc = Document(html, url=url)
        summary_html = doc.summary()

        # Parse the summary HTML and extract text
        tree = document_fromstring(summary_html)
        text = tree.text_content()

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)
    except Exception as e:
        logger.warning(
            "readability-lxml extraction failed: %s. Falling back.", e
        )
        return _basic_html_to_text(html)


def _basic_html_to_text(html: str) -> str:
    """Fallback: strip HTML tags for basic text extraction."""
    from html.parser import HTMLParser

    class TextExtractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []
            self._skip = False

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag in ("script", "style", "noscript"):
                self._skip = True

        def handle_endtag(self, tag: str) -> None:
            if tag in ("script", "style", "noscript"):
                self._skip = False

        def handle_data(self, data: str) -> None:
            if not self._skip:
                self.parts.append(data)

    extractor = TextExtractor()
    extractor.feed(html)
    text = " ".join(extractor.parts)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _looks_like_spa(html: str) -> bool:
    """Heuristic check for SPA/JS-heavy pages."""
    lower = html.lower()
    # Common SPA indicators
    spa_markers = [
        "window.__initial_state__",
        "window.__next_data__",
        "__nuxt",
        "react-root",
        'id="app"',
        'id="root"',
        "ng-app",
    ]
    # If the body is very small but has lots of script tags, probably SPA
    body_text_ratio = len(re.sub(r"<[^>]+>", "", html)) / max(len(html), 1)
    if body_text_ratio < 0.1:
        return True
    return any(marker in lower for marker in spa_markers)
