"""Detect standard resume sections from extracted text.

Why:
    ATS systems look for standard section headers (Experience, Education, Skills).
    Section detection feeds into both structure scoring (are standard sections
    present?) and keyword matching (which section contains what content?).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from anvilcv.scoring.text_extractor import ExtractedDocument

# Standard section header patterns — each maps to a canonical section name.
# Patterns are case-insensitive and match common variations.
SECTION_PATTERNS: dict[str, list[str]] = {
    "experience": [
        r"(?:work\s+)?experience",
        r"employment(?:\s+history)?",
        r"work\s+history",
        r"professional\s+(?:experience|background)",
    ],
    "education": [
        r"education",
        r"academic(?:\s+background)?",
        r"degrees?",
        r"qualifications",
    ],
    "skills": [
        r"(?:technical\s+)?skills",
        r"technologies",
        r"competenc(?:ies|e)",
        r"tools?\s*(?:&|and)\s*technologies",
        r"tech(?:nical)?\s+stack",
    ],
    "projects": [
        r"projects?",
        r"personal\s+projects?",
        r"side\s+projects?",
        r"portfolio",
    ],
    "summary": [
        r"summary",
        r"objective",
        r"profile",
        r"about(?:\s+me)?",
        r"professional\s+summary",
    ],
    "certifications": [
        r"certifications?",
        r"licenses?\s*(?:&|and)\s*certifications?",
        r"professional\s+certifications?",
    ],
    "publications": [
        r"publications?",
        r"papers?",
        r"research",
    ],
    "awards": [
        r"awards?(?:\s*(?:&|and)\s*honors?)?",
        r"honors?(?:\s*(?:&|and)\s*awards?)?",
        r"achievements?",
    ],
    "volunteer": [
        r"volunteer(?:ing)?(?:\s+(?:experience|work))?",
        r"community\s+(?:service|involvement)",
    ],
    "contact": [
        r"contact(?:\s+(?:info(?:rmation)?|details?))?",
    ],
}

# Compile patterns once
_COMPILED_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    section: [re.compile(p, re.IGNORECASE) for p in patterns]
    for section, patterns in SECTION_PATTERNS.items()
}


@dataclass
class DetectedSection:
    """A detected resume section."""

    name: str  # Canonical section name (e.g., "experience")
    header_text: str  # Actual header text found
    line_index: int  # Line index in the document
    is_standard: bool = True  # Whether it uses a standard header name


@dataclass
class SectionMap:
    """Map of all detected sections in a document."""

    sections: list[DetectedSection] = field(default_factory=list)

    def has_section(self, name: str) -> bool:
        """Check if a canonical section was detected."""
        return any(s.name == name for s in self.sections)

    def get_section(self, name: str) -> DetectedSection | None:
        """Get a detected section by canonical name."""
        for s in self.sections:
            if s.name == name:
                return s
        return None

    @property
    def section_names(self) -> list[str]:
        """List of canonical section names detected."""
        return [s.name for s in self.sections]


def _is_likely_header(line: str) -> bool:
    """Check if a line looks like a section header.

    Headers tend to be short, may be uppercase, and don't end with
    common sentence-ending punctuation.
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return False
    # Reject lines that look like regular sentences
    if stripped.endswith(("..", "...", ";")):
        return False
    return True


def detect_sections(doc: ExtractedDocument) -> SectionMap:
    """Detect resume sections from extracted document text."""
    sections: list[DetectedSection] = []
    seen: set[str] = set()

    for i, line in enumerate(doc.lines):
        if not _is_likely_header(line):
            continue

        # Strip common decorators (bullets, dashes, colons)
        clean = re.sub(r"^[\s\-•·:]+|[\s:]+$", "", line).strip()
        if not clean:
            continue

        for section_name, patterns in _COMPILED_PATTERNS.items():
            if section_name in seen:
                continue
            for pattern in patterns:
                if pattern.fullmatch(clean):
                    sections.append(
                        DetectedSection(
                            name=section_name,
                            header_text=line.strip(),
                            line_index=i,
                            is_standard=True,
                        )
                    )
                    seen.add(section_name)
                    break
            if section_name in seen:
                break

    return SectionMap(sections=sections)
