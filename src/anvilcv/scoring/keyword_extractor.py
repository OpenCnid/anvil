"""Heuristic keyword extraction from job descriptions.

Why:
    Extracts skills and requirements from job description text using
    a curated taxonomy. This is the heuristic pipeline — no AI required.
    The taxonomy is the ONLY source of keyword aliases.
"""

from __future__ import annotations

import pathlib
import re

import yaml  # type: ignore[import-untyped]

_TAXONOMY_PATH = pathlib.Path(__file__).parent / "skills_taxonomy.yaml"
_taxonomy_cache: dict[str, list[dict]] | None = None


def _load_taxonomy() -> dict[str, list[dict]]:
    """Load and cache the skills taxonomy."""
    global _taxonomy_cache
    if _taxonomy_cache is None:
        with open(_TAXONOMY_PATH) as f:
            _taxonomy_cache = yaml.safe_load(f)
    return _taxonomy_cache


def _build_alias_map() -> dict[str, str]:
    """Build a lowercase alias → canonical name mapping."""
    taxonomy = _load_taxonomy()
    alias_map: dict[str, str] = {}
    for _category, skills in taxonomy.items():
        if not isinstance(skills, list):
            continue
        for skill in skills:
            name = skill["name"]
            # Map the canonical name itself
            alias_map[name.lower()] = name
            for alias in skill.get("aliases", []):
                alias_map[alias.lower()] = name
    return alias_map


# Build once at import time
_ALIAS_MAP = _build_alias_map()

# Patterns for extracting experience requirements
_EXPERIENCE_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)",
    re.IGNORECASE,
)

# Section headers that indicate requirements
_REQUIREMENT_HEADERS = re.compile(
    r"(?:requirements?|qualifications?|what\s+you.?(?:ll|will)\s+"
    r"(?:need|bring)|must\s+have|minimum)",
    re.IGNORECASE,
)

_PREFERRED_HEADERS = re.compile(
    r"(?:nice\s+to\s+have|preferred|bonus|ideal|plus)",
    re.IGNORECASE,
)


def extract_skills(text: str) -> list[str]:
    """Extract skill keywords from text using the taxonomy.

    Returns deduplicated canonical skill names found in the text.
    """
    text_lower = text.lower()
    found: dict[str, str] = {}  # canonical_lower -> canonical_name

    for alias, canonical in _ALIAS_MAP.items():
        if canonical.lower() in found:
            continue
        # Word boundary matching for short aliases to avoid false positives
        if len(alias) <= 2:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, text_lower):
                found[canonical.lower()] = canonical
        elif alias in text_lower:
            found[canonical.lower()] = canonical

    return list(found.values())


def extract_experience_years(text: str) -> int | None:
    """Extract years of experience requirement from text."""
    match = _EXPERIENCE_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return None


def categorize_skills(
    text: str,
) -> tuple[list[str], list[str]]:
    """Categorize skills into required and preferred.

    Splits text by requirement/preferred section headers and extracts
    skills from each section. If no clear sections, all skills are
    treated as required.

    Returns:
        Tuple of (required_skills, preferred_skills).
    """
    lines = text.split("\n")
    required_lines: list[str] = []
    preferred_lines: list[str] = []
    current_section = "required"

    for line in lines:
        if _REQUIREMENT_HEADERS.search(line):
            current_section = "required"
        elif _PREFERRED_HEADERS.search(line):
            current_section = "preferred"

        if current_section == "preferred":
            preferred_lines.append(line)
        else:
            required_lines.append(line)

    required_text = "\n".join(required_lines)
    preferred_text = "\n".join(preferred_lines)

    required_skills = extract_skills(required_text)
    preferred_skills = extract_skills(preferred_text)

    # Deduplicate: if a skill is in both, keep only in required
    required_set = {s.lower() for s in required_skills}
    preferred_skills = [s for s in preferred_skills if s.lower() not in required_set]

    return required_skills, preferred_skills
