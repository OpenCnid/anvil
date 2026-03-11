"""ATS scorer engine — orchestrates the full scoring pipeline.

Why:
    The scorer is the main entry point for ATS compatibility analysis.
    It coordinates text extraction → section detection → parsability checks
    → structure checks → score calculation into a unified ScoreReport.
"""

from __future__ import annotations

import pathlib
from datetime import datetime

from anvilcv.schema.score_report import (
    Check,
    ScoreReport,
    SectionScore,
)
from anvilcv.scoring.parsability_checker import run_parsability_checks
from anvilcv.scoring.section_detector import detect_sections
from anvilcv.scoring.structure_checker import run_structure_checks
from anvilcv.scoring.text_extractor import ExtractedDocument, extract_text


def _calculate_category_score(checks: list[Check]) -> int:
    """Calculate a category score from its checks.

    Each rule passes (1.0), warns (0.5), or fails (0.0).
    Score = (sum / total) * 100.
    """
    if not checks:
        return 0

    total = 0.0
    for check in checks:
        if check.status == "pass":
            total += 1.0
        elif check.status == "warn":
            total += 0.5

    return round((total / len(checks)) * 100)


def _calculate_overall_score(
    parsability_score: int,
    structure_score: int,
    keyword_score: int | None = None,
) -> int:
    """Calculate overall score with appropriate weights.

    With job description: 40% parsability + 30% structure + 30% keywords
    Without: 55% parsability + 45% structure
    """
    if keyword_score is not None:
        return round(
            parsability_score * 0.40
            + structure_score * 0.30
            + keyword_score * 0.30
        )
    return round(parsability_score * 0.55 + structure_score * 0.45)


def score_document(path: pathlib.Path) -> ScoreReport:
    """Score a document for ATS compatibility.

    Runs the full pipeline: extraction → section detection →
    parsability + structure checks → score calculation.
    """
    doc = extract_text(path)
    return score_extracted_document(doc, file_path=str(path))


def score_extracted_document(
    doc: ExtractedDocument,
    file_path: str = "",
) -> ScoreReport:
    """Score an already-extracted document."""
    sections = detect_sections(doc)

    parsability_checks = run_parsability_checks(doc)
    structure_checks = run_structure_checks(doc, sections)

    parsability_score = _calculate_category_score(parsability_checks)
    structure_score = _calculate_category_score(structure_checks)
    overall = _calculate_overall_score(parsability_score, structure_score)

    return ScoreReport(
        file=file_path,
        scored_at=datetime.now(),
        overall_score=overall,
        parsability=SectionScore(
            score=parsability_score,
            checks=parsability_checks,
        ),
        structure=SectionScore(
            score=structure_score,
            checks=structure_checks,
        ),
    )
