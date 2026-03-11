"""Extract text from PDF and HTML files for ATS scoring.

Why:
    The ATS scorer operates on rendered output (PDF or HTML), not raw YAML.
    We extract text with position data for layout analysis (single-column
    detection, reading order) and content analysis (section detection).
"""

from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass, field
from html.parser import HTMLParser

from anvilcv.exceptions import AnvilUserError

logger = logging.getLogger(__name__)


@dataclass
class TextElement:
    """A positioned text element extracted from a document."""

    text: str
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    font_name: str | None = None
    font_size: float | None = None
    page: int = 1


@dataclass
class ExtractedDocument:
    """Complete text extraction result from a document."""

    elements: list[TextElement] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 1
    source_type: str = "unknown"
    has_tables: bool = False
    has_images: bool = False
    fonts_used: set[str] = field(default_factory=set)
    image_page_count: int = 0

    @property
    def lines(self) -> list[str]:
        """Split full text into non-empty lines."""
        return [line for line in self.full_text.splitlines() if line.strip()]

    @property
    def is_empty(self) -> bool:
        """True if no meaningful text was extracted."""
        return not self.full_text.strip()

    @property
    def is_partial(self) -> bool:
        """True if some pages appear to be images with no extractable text."""
        return self.image_page_count > 0 and not self.is_empty


def extract_from_pdf(path: pathlib.Path) -> ExtractedDocument:
    """Extract text with position data from a PDF file.

    Uses pdfminer.six for text extraction. Preserves position data
    for layout analysis (single-column detection, reading order).
    """
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LAParams, LTChar, LTFigure, LTTextBox, LTTextLine

    if not path.exists():
        raise AnvilUserError(message=f"File not found: {path}")

    elements: list[TextElement] = []
    full_text_parts: list[str] = []
    page_count = 0
    fonts_used: set[str] = set()
    has_images = False
    has_tables = False
    image_page_count = 0

    laparams = LAParams(
        line_margin=0.5,
        word_margin=0.1,
        char_margin=2.0,
        boxes_flow=0.5,
    )

    for page_layout in extract_pages(str(path), laparams=laparams):
        page_count += 1
        page_has_text = False
        page_has_figure = False
        for element in page_layout:
            if isinstance(element, LTTextBox):
                for line in element:
                    if isinstance(line, LTTextLine):
                        text = line.get_text().strip()
                        if not text:
                            continue

                        page_has_text = True
                        font_name = None
                        font_size = None
                        for char in line:
                            if isinstance(char, LTChar):
                                font_name = char.fontname
                                font_size = char.size
                                fonts_used.add(char.fontname)
                                break

                        elements.append(
                            TextElement(
                                text=text,
                                x=line.x0,
                                y=line.y0,
                                width=line.x1 - line.x0,
                                height=line.y1 - line.y0,
                                font_name=font_name,
                                font_size=font_size,
                                page=page_count,
                            )
                        )
                        full_text_parts.append(text)

            elif isinstance(element, LTFigure):
                has_images = True
                page_has_figure = True

        # A page with figures but no text is likely an image/scanned page
        if page_has_figure and not page_has_text:
            image_page_count += 1

    return ExtractedDocument(
        elements=elements,
        full_text="\n".join(full_text_parts),
        page_count=max(page_count, 1),
        source_type="pdf",
        has_tables=has_tables,
        has_images=has_images,
        fonts_used=fonts_used,
        image_page_count=image_page_count,
    )


class _HTMLTextExtractor(HTMLParser):
    """Simple HTML parser that extracts text content."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.elements: list[TextElement] = []
        self.has_tables = False
        self._current_tag: str | None = None
        self._skip_tags = {"script", "style", "head"}
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._current_tag = tag
        if tag in self._skip_tags:
            self._skip_depth += 1
        if tag == "table":
            self.has_tables = True

    def handle_endtag(self, tag: str) -> None:
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.strip()
        if text:
            self.text_parts.append(text)
            self.elements.append(TextElement(text=text))


def extract_from_html(path: pathlib.Path) -> ExtractedDocument:
    """Extract text from an HTML file."""
    if not path.exists():
        raise AnvilUserError(message=f"File not found: {path}")

    content = path.read_text(encoding="utf-8")
    parser = _HTMLTextExtractor()
    parser.feed(content)

    return ExtractedDocument(
        elements=parser.elements,
        full_text="\n".join(parser.text_parts),
        page_count=1,
        source_type="html",
        has_tables=parser.has_tables,
    )


def extract_text(path: pathlib.Path) -> ExtractedDocument:
    """Extract text from a file, auto-detecting format by extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_from_pdf(path)
    elif suffix in (".html", ".htm"):
        return extract_from_html(path)
    else:
        raise AnvilUserError(
            message=(
                f"Unsupported format. Provide a .pdf, .html, or .yaml file, "
                f"not '{suffix}'."
            )
        )
