"""Structure scoring rules S-01 through S-08.

Why:
    Structure scoring evaluates whether standard resume sections are
    present and properly organized. ATS systems map content to predefined
    fields — missing or unconventional sections reduce parsing accuracy.
"""

from __future__ import annotations

import re

from anvilcv.schema.score_report import Check
from anvilcv.scoring.section_detector import SectionMap
from anvilcv.scoring.text_extractor import ExtractedDocument

# Contact info patterns
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
)
URL_PATTERN = re.compile(r"https?://\S+|(?:linkedin|github)\.com/\S+", re.IGNORECASE)

# Date patterns for chronological ordering check
DATE_PATTERN = re.compile(
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{4}",
    re.IGNORECASE,
)
ABBREVIATED_DATE = re.compile(
    r"\b(?:jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b(?!\w)",
    re.IGNORECASE,
)
FULL_DATE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b",
    re.IGNORECASE,
)


def check_s01_contact_info(doc: ExtractedDocument) -> Check:
    """S-01: Detect name, email, phone, location."""
    text = doc.full_text
    has_email = bool(EMAIL_PATTERN.search(text))
    has_phone = bool(PHONE_PATTERN.search(text))

    if has_email and has_phone:
        return Check(
            name="Contact information present",
            status="pass",
            confidence="evidence_based",
        )
    elif has_email or has_phone:
        missing = "phone" if not has_phone else "email"
        return Check(
            name="Contact information present",
            status="warn",
            confidence="evidence_based",
            detail=f"Missing {missing} in detected contact information.",
        )
    else:
        return Check(
            name="Contact information present",
            status="fail",
            confidence="evidence_based",
            detail="No email or phone number detected.",
        )


def check_s02_experience_section(sections: SectionMap) -> Check:
    """S-02: Look for Experience section."""
    if sections.has_section("experience"):
        return Check(
            name="Experience section detected",
            status="pass",
            confidence="evidence_based",
        )
    return Check(
        name="Experience section detected",
        status="fail",
        confidence="evidence_based",
        detail="No experience section header found.",
    )


def check_s03_education_section(sections: SectionMap) -> Check:
    """S-03: Look for Education section."""
    if sections.has_section("education"):
        return Check(
            name="Education section detected",
            status="pass",
            confidence="evidence_based",
        )
    return Check(
        name="Education section detected",
        status="fail",
        confidence="evidence_based",
        detail="No education section header found.",
    )


def check_s04_skills_section(sections: SectionMap) -> Check:
    """S-04: Look for Skills section."""
    if sections.has_section("skills"):
        return Check(
            name="Skills section detected",
            status="pass",
            confidence="opinionated_heuristic",
        )
    return Check(
        name="Skills section detected",
        status="warn",
        confidence="opinionated_heuristic",
        detail="No skills section header found. Most ATS benefit from a skills section.",
    )


def check_s05_standard_headers(sections: SectionMap) -> Check:
    """S-05: Check if section headers use conventional names."""
    if not sections.sections:
        return Check(
            name="Standard section headers",
            status="warn",
            confidence="opinionated_heuristic",
            detail="No standard section headers detected.",
        )

    non_standard = [s for s in sections.sections if not s.is_standard]
    if non_standard:
        names = ", ".join(f'"{s.header_text}"' for s in non_standard[:3])
        return Check(
            name="Standard section headers",
            status="warn",
            confidence="opinionated_heuristic",
            detail=f"Non-standard section headers: {names}.",
        )

    return Check(
        name="Standard section headers",
        status="pass",
        confidence="opinionated_heuristic",
    )


def check_s06_chronological_dates(doc: ExtractedDocument) -> Check:
    """S-06: Check if entries are in reverse-chronological order."""
    dates = DATE_PATTERN.findall(doc.full_text)
    if len(dates) < 2:
        return Check(
            name="Chronological date ordering",
            status="pass",
            confidence="opinionated_heuristic",
            detail="Insufficient dates to verify ordering.",
        )

    # Parse years from dates and check they're generally descending
    years = []
    for date_str in dates:
        parts = date_str.split()
        if len(parts) >= 2:
            try:
                years.append(int(parts[-1]))
            except ValueError:
                continue

    if len(years) >= 2:
        # Allow some flexibility — not strictly monotonic
        inversions = sum(
            1 for i in range(len(years) - 1) if years[i] < years[i + 1]
        )
        if inversions > len(years) // 3:
            return Check(
                name="Chronological date ordering",
                status="warn",
                confidence="opinionated_heuristic",
                detail="Dates may not be in reverse-chronological order.",
            )

    return Check(
        name="Chronological date ordering",
        status="pass",
        confidence="opinionated_heuristic",
    )


def check_s07_machine_readable_dates(doc: ExtractedDocument) -> Check:
    """S-07: Check date format consistency."""
    text = doc.full_text
    abbreviated = ABBREVIATED_DATE.findall(text)
    full = FULL_DATE.findall(text)

    if abbreviated and not full:
        return Check(
            name="Machine-readable dates",
            status="warn",
            confidence="opinionated_heuristic",
            detail=(
                f"Abbreviated month names detected ({abbreviated[0]}). "
                "Full month names are safer for ATS parsing."
            ),
        )

    if abbreviated and full:
        return Check(
            name="Machine-readable dates",
            status="warn",
            confidence="opinionated_heuristic",
            detail="Mixed date formats detected. Consistency is recommended.",
        )

    return Check(
        name="Machine-readable dates",
        status="pass",
        confidence="opinionated_heuristic",
    )


def check_s08_resume_length(doc: ExtractedDocument) -> Check:
    """S-08: Check page count (1-2 pages for most candidates)."""
    pages = doc.page_count
    if pages == 1:
        return Check(
            name="Resume length",
            status="pass",
            confidence="opinionated_heuristic",
            detail="1 page.",
        )
    elif pages == 2:
        return Check(
            name="Resume length",
            status="pass",
            confidence="opinionated_heuristic",
            detail="2 pages.",
        )
    elif pages > 2:
        return Check(
            name="Resume length",
            status="warn",
            confidence="opinionated_heuristic",
            detail=f"{pages} pages. 1-2 pages is recommended for most candidates.",
        )

    return Check(
        name="Resume length",
        status="pass",
        confidence="opinionated_heuristic",
    )


def run_structure_checks(
    doc: ExtractedDocument, sections: SectionMap
) -> list[Check]:
    """Run all structure checks and return results."""
    return [
        check_s01_contact_info(doc),
        check_s02_experience_section(sections),
        check_s03_education_section(sections),
        check_s04_skills_section(sections),
        check_s05_standard_headers(sections),
        check_s06_chronological_dates(doc),
        check_s07_machine_readable_dates(doc),
        check_s08_resume_length(doc),
    ]
