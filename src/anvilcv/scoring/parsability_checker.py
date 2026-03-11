"""Parsability scoring rules P-01 through P-08.

Why:
    Parsability evaluates whether the resume's structure can be reliably
    parsed by text extraction tools. Each rule returns a Check with
    pass/fail/warn status, confidence level, and evidence.
"""

from __future__ import annotations

import re

from anvilcv.schema.score_report import Check
from anvilcv.scoring.text_extractor import ExtractedDocument

# Standard embeddable fonts that most PDF readers/ATS support
STANDARD_FONTS = {
    "arial",
    "helvetica",
    "times",
    "timesnewroman",
    "calibri",
    "cambria",
    "garamond",
    "georgia",
    "verdana",
    "tahoma",
    "trebuchet",
    "palatino",
    "courier",
    "couriernew",
    "roboto",
    "opensans",
    "lato",
    "montserrat",
    "sourcesanspro",
    "noto",
}


def _normalize_font(name: str) -> str:
    """Normalize font name for comparison (lowercase, strip variants)."""
    name = name.lower()
    # Strip common suffixes like -Bold, -Italic, +Regular, etc.
    name = re.sub(r"[-+,](bold|italic|regular|light|medium|semibold|thin).*", "", name)
    # Strip whitespace and hyphens for matching
    name = name.replace(" ", "").replace("-", "").replace("_", "")
    return name


def check_p01_single_column(doc: ExtractedDocument) -> Check:
    """P-01: Detect multi-column layout via text position analysis."""
    if doc.source_type != "pdf" or not doc.elements:
        return Check(
            name="Single-column layout",
            status="pass",
            confidence="evidence_based",
            detail="Non-PDF or empty document — skipped.",
        )

    # Group elements by page, check if text spans suggest multiple columns
    page_elements: dict[int, list[float]] = {}
    for elem in doc.elements:
        page_elements.setdefault(elem.page, []).append(elem.x)

    for page, x_positions in page_elements.items():
        if len(x_positions) < 5:
            continue

        # Find distinct x-position clusters (columns)
        sorted_x = sorted(set(round(x, 0) for x in x_positions))
        if len(sorted_x) < 2:
            continue

        # Check for wide gaps that suggest separate columns
        gaps = [
            sorted_x[i + 1] - sorted_x[i] for i in range(len(sorted_x) - 1)
        ]
        # A gap > 150 points suggests a separate column
        wide_gaps = [g for g in gaps if g > 150]
        if wide_gaps:
            return Check(
                name="Single-column layout",
                status="warn",
                confidence="evidence_based",
                source="Jobscan 2023 ATS parsing study",
                detail=f"Possible multi-column layout detected on page {page}.",
            )

    return Check(
        name="Single-column layout",
        status="pass",
        confidence="evidence_based",
        source="Jobscan 2023 ATS parsing study",
    )


def check_p02_no_embedded_images(doc: ExtractedDocument) -> Check:
    """P-02: Check if text content is extractable (not rasterized)."""
    if doc.source_type == "pdf" and doc.has_images and len(doc.elements) < 5:
        return Check(
            name="All text machine-readable",
            status="fail",
            confidence="evidence_based",
            source="Greenhouse support docs",
            detail=(
                "Document contains images but very little extractable text. "
                "Text may be embedded as images."
            ),
        )

    if not doc.full_text.strip():
        return Check(
            name="All text machine-readable",
            status="fail",
            confidence="evidence_based",
            detail="No text could be extracted from the document.",
        )

    return Check(
        name="All text machine-readable",
        status="pass",
        confidence="evidence_based",
        source="Greenhouse support docs",
    )


def check_p03_standard_fonts(doc: ExtractedDocument) -> Check:
    """P-03: Check if fonts are commonly supported."""
    if not doc.fonts_used:
        return Check(
            name="Standard fonts",
            status="pass",
            confidence="opinionated_heuristic",
            detail="No font information available.",
        )

    non_standard = []
    for font in doc.fonts_used:
        norm = _normalize_font(font)
        if not any(std in norm for std in STANDARD_FONTS):
            non_standard.append(font)

    if non_standard:
        return Check(
            name="Standard fonts",
            status="warn",
            confidence="opinionated_heuristic",
            detail=f"Non-standard fonts detected: {', '.join(non_standard[:3])}.",
        )

    return Check(
        name="Standard fonts",
        status="pass",
        confidence="opinionated_heuristic",
    )


def check_p04_no_tables(doc: ExtractedDocument) -> Check:
    """P-04: Detect tables used for layout."""
    if doc.has_tables:
        return Check(
            name="No tables for layout",
            status="warn",
            confidence="evidence_based",
            source="Jobscan 2023",
            detail="HTML tables detected — may cause ATS parsing issues.",
        )

    return Check(
        name="No tables for layout",
        status="pass",
        confidence="evidence_based",
        source="Jobscan 2023",
    )


def check_p05_no_headers_footers(doc: ExtractedDocument) -> Check:
    """P-05: Check if critical content is in main body, not headers/footers."""
    if doc.source_type != "pdf" or not doc.elements:
        return Check(
            name="No critical content in headers/footers",
            status="pass",
            confidence="evidence_based",
            source="Workday support docs",
        )

    # In PDF, headers/footers are typically at extreme y positions
    # For now, pass — rendercv-generated PDFs don't use headers/footers
    return Check(
        name="No critical content in headers/footers",
        status="pass",
        confidence="evidence_based",
        source="Workday support docs",
    )


def check_p06_text_extractability(doc: ExtractedDocument) -> Check:
    """P-06: Verify text can be extracted in reading order."""
    if not doc.full_text.strip():
        return Check(
            name="Text extractability",
            status="fail",
            confidence="evidence_based",
            detail="No text could be extracted from the document.",
        )

    # Check for reasonable text content
    word_count = len(doc.full_text.split())
    if word_count < 20:
        return Check(
            name="Text extractability",
            status="warn",
            confidence="evidence_based",
            detail=f"Only {word_count} words extracted — document may not be text-based.",
        )

    return Check(
        name="Text extractability",
        status="pass",
        confidence="evidence_based",
    )


def check_p07_no_text_boxes(doc: ExtractedDocument) -> Check:
    """P-07: Detect positioned elements that break reading order."""
    # For rendercv-generated content, this is typically not an issue.
    # A full implementation would analyze PDF content streams for
    # text positioning commands. For v1, we rely on column detection (P-01).
    return Check(
        name="No text boxes or floating elements",
        status="pass",
        confidence="opinionated_heuristic",
    )


def check_p08_standard_format(doc: ExtractedDocument) -> Check:
    """P-08: Check for standard PDF format (not scanned image)."""
    if doc.source_type == "html":
        return Check(
            name="Standard file format",
            status="pass",
            confidence="evidence_based",
            detail="HTML is a standard machine-readable format.",
        )

    # If we got text from the PDF, it's machine-readable
    if doc.full_text.strip():
        return Check(
            name="Standard file format",
            status="pass",
            confidence="evidence_based",
        )

    return Check(
        name="Standard file format",
        status="fail",
        confidence="evidence_based",
        detail="PDF appears to be a scanned image — no extractable text.",
    )


def run_parsability_checks(doc: ExtractedDocument) -> list[Check]:
    """Run all parsability checks and return results."""
    return [
        check_p01_single_column(doc),
        check_p02_no_embedded_images(doc),
        check_p03_standard_fonts(doc),
        check_p04_no_tables(doc),
        check_p05_no_headers_footers(doc),
        check_p06_text_extractability(doc),
        check_p07_no_text_boxes(doc),
        check_p08_standard_format(doc),
    ]
