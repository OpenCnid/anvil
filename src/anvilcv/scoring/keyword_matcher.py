"""Keyword matching scoring rules K-01 through K-05.

Why:
    Keyword matching evaluates how well a resume matches a job description's
    requirements. This is only calculated when a job description is provided.
"""

from __future__ import annotations

import re

from anvilcv.schema.score_report import Check, KeywordMatchSection
from anvilcv.scoring.keyword_extractor import extract_skills
from anvilcv.scoring.text_extractor import ExtractedDocument

# Action verbs that show impact
STRONG_ACTION_VERBS = {
    "built",
    "designed",
    "developed",
    "implemented",
    "led",
    "launched",
    "shipped",
    "created",
    "architected",
    "optimized",
    "migrated",
    "automated",
    "scaled",
    "reduced",
    "increased",
    "improved",
    "delivered",
    "deployed",
    "managed",
    "mentored",
    "collaborated",
    "established",
    "streamlined",
    "refactored",
    "spearheaded",
    "pioneered",
    "orchestrated",
    "transformed",
    "achieved",
    "accelerated",
}

WEAK_PATTERNS = [
    "responsible for",
    "duties included",
    "helped with",
    "assisted in",
    "participated in",
    "worked on",
    "involved in",
]


def check_k01_required_skills(
    resume_skills: list[str],
    required_skills: list[str],
) -> tuple[Check, list[str], list[str]]:
    """K-01: Match job's required skills against resume content."""
    if not required_skills:
        return (
            Check(
                name="Required skill keywords",
                status="pass",
                confidence="evidence_based",
                source="Greenhouse, Lever",
                detail="No required skills specified in job description.",
            ),
            [],
            [],
        )

    resume_lower = {s.lower() for s in resume_skills}
    matched = [s for s in required_skills if s.lower() in resume_lower]
    missing = [s for s in required_skills if s.lower() not in resume_lower]

    ratio = len(matched) / len(required_skills) if required_skills else 0

    if ratio >= 0.8:
        status = "pass"
    elif ratio >= 0.5:
        status = "warn"
    else:
        status = "fail"

    return (
        Check(
            name="Required skill keywords",
            status=status,
            confidence="evidence_based",
            source="Greenhouse, Lever",
            detail=(
                f"Matched {len(matched)}/{len(required_skills)} required skills."
            ),
        ),
        matched,
        missing,
    )


def check_k02_preferred_skills(
    resume_skills: list[str],
    preferred_skills: list[str],
) -> Check:
    """K-02: Match job's preferred/nice-to-have skills."""
    if not preferred_skills:
        return Check(
            name="Preferred skill keywords",
            status="pass",
            confidence="evidence_based",
            source="Greenhouse, Lever",
            detail="No preferred skills specified.",
        )

    resume_lower = {s.lower() for s in resume_skills}
    matched = sum(1 for s in preferred_skills if s.lower() in resume_lower)
    ratio = matched / len(preferred_skills)

    if ratio >= 0.5:
        status = "pass"
    elif ratio >= 0.25:
        status = "warn"
    else:
        status = "fail"

    return Check(
        name="Preferred skill keywords",
        status=status,
        confidence="evidence_based",
        source="Greenhouse, Lever",
        detail=f"Matched {matched}/{len(preferred_skills)} preferred skills.",
    )


def check_k03_job_title(
    resume_text: str,
    job_title: str,
) -> Check:
    """K-03: Check if resume contains the target job title."""
    if not job_title:
        return Check(
            name="Job title alignment",
            status="pass",
            confidence="opinionated_heuristic",
        )

    title_lower = job_title.lower()
    text_lower = resume_text.lower()

    # Check for exact title
    if title_lower in text_lower:
        return Check(
            name="Job title alignment",
            status="pass",
            confidence="opinionated_heuristic",
            detail=f'Job title "{job_title}" found in resume.',
        )

    # Check for individual significant words (3+ chars)
    words = [w for w in title_lower.split() if len(w) >= 3]
    matched = sum(1 for w in words if w in text_lower)
    if matched >= len(words) * 0.5:
        return Check(
            name="Job title alignment",
            status="warn",
            confidence="opinionated_heuristic",
            detail=f"Partial job title match ({matched}/{len(words)} keywords).",
        )

    return Check(
        name="Job title alignment",
        status="fail",
        confidence="opinionated_heuristic",
        detail=f'Job title "{job_title}" not found in resume.',
    )


def check_k04_industry_terms(
    resume_text: str,
    job_text: str,
) -> Check:
    """K-04: Check for industry-specific terms from the job description."""
    job_skills = extract_skills(job_text)
    resume_skills = extract_skills(resume_text)

    if not job_skills:
        return Check(
            name="Industry terminology",
            status="pass",
            confidence="opinionated_heuristic",
        )

    job_set = {s.lower() for s in job_skills}
    resume_set = {s.lower() for s in resume_skills}
    overlap = job_set & resume_set

    ratio = len(overlap) / len(job_set) if job_set else 0

    if ratio >= 0.6:
        status = "pass"
    elif ratio >= 0.3:
        status = "warn"
    else:
        status = "fail"

    return Check(
        name="Industry terminology",
        status=status,
        confidence="opinionated_heuristic",
        detail=f"Matched {len(overlap)}/{len(job_set)} industry terms.",
    )


def check_k05_action_verbs(resume_text: str) -> Check:
    """K-05: Check for strong action verbs."""
    text_lower = resume_text.lower()

    strong_found = sum(
        1
        for verb in STRONG_ACTION_VERBS
        if re.search(rf"\b{verb}\b", text_lower)
    )

    weak_found = sum(1 for p in WEAK_PATTERNS if p in text_lower)

    if strong_found >= 5 and weak_found <= 1:
        return Check(
            name="Action verb usage",
            status="pass",
            confidence="opinionated_heuristic",
            detail=f"Found {strong_found} strong action verbs.",
        )
    elif strong_found >= 3:
        return Check(
            name="Action verb usage",
            status="warn",
            confidence="opinionated_heuristic",
            detail=(
                f"Found {strong_found} strong action verbs"
                f" and {weak_found} weak phrases."
            ),
        )
    else:
        return Check(
            name="Action verb usage",
            status="fail",
            confidence="opinionated_heuristic",
            detail=(
                f"Only {strong_found} strong action verbs found. "
                "Use more impactful language."
            ),
        )


def run_keyword_checks(
    doc: ExtractedDocument,
    job_text: str,
    job_title: str = "",
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
) -> tuple[list[Check], KeywordMatchSection]:
    """Run all keyword matching checks.

    Returns checks and a KeywordMatchSection summary.
    """
    resume_skills = extract_skills(doc.full_text)
    required = required_skills or []
    preferred = preferred_skills or []

    k01_check, matched, missing = check_k01_required_skills(
        resume_skills, required
    )
    k02_check = check_k02_preferred_skills(resume_skills, preferred)
    k03_check = check_k03_job_title(doc.full_text, job_title)
    k04_check = check_k04_industry_terms(doc.full_text, job_text)
    k05_check = check_k05_action_verbs(doc.full_text)

    checks = [k01_check, k02_check, k03_check, k04_check, k05_check]

    # Calculate keyword score from checks
    total = 0.0
    for check in checks:
        if check.status == "pass":
            total += 1.0
        elif check.status == "warn":
            total += 0.5
    score = round((total / len(checks)) * 100)

    section = KeywordMatchSection(
        score=score,
        job_keywords=required + preferred,
        matched=matched,
        missing=missing,
    )

    return checks, section
