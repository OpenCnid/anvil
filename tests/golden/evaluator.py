"""Golden-set rubric evaluator for Tier 2 regression tests.

Why:
    Provides deterministic + LLM-as-judge scoring to validate AI feature output
    quality. Deterministic checks (keyword_presence, structural_check,
    factual_accuracy) give fast, reproducible signals. Subjective_quality
    criteria use an LLM-as-judge for nuanced assessment. Together they produce
    a weighted 0-100 score per test case, enabling regression tracking across
    nightly runs.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

logger = logging.getLogger(__name__)

yaml = YAML()
yaml.preserve_quotes = True


@dataclass
class CriterionResult:
    """Result of evaluating a single rubric criterion."""

    name: str
    criterion_type: str
    weight: float
    score: float  # 0.0-1.0
    evidence: str = ""


@dataclass
class EvaluationResult:
    """Full evaluation result for a golden-set test case."""

    case_name: str
    feature: str
    provider: str
    total_score: float  # 0-100
    criterion_results: list[CriterionResult] = field(default_factory=list)
    raw_output: str = ""


def load_rubric(rubric_path: Path) -> list[dict[str, Any]]:
    """Load evaluation rubric from YAML file."""
    with open(rubric_path) as f:
        data = yaml.load(f)
    return data.get("rubric", [])


def evaluate_keyword_presence(output: str, criterion: dict[str, Any]) -> CriterionResult:
    """Check if required keywords are present in output.

    Criterion format:
        keywords: list of strings to find (case-insensitive)
        min_matches: minimum number that must be present (default: all)
    """
    keywords = criterion.get("keywords", [])
    min_matches = criterion.get("min_matches", len(keywords))
    found = []
    missing = []

    for kw in keywords:
        if re.search(re.escape(kw), output, re.IGNORECASE):
            found.append(kw)
        else:
            missing.append(kw)

    match_count = len(found)
    score = min(match_count / max(min_matches, 1), 1.0)

    return CriterionResult(
        name=criterion["criterion"],
        criterion_type="keyword_presence",
        weight=criterion["weight"],
        score=score,
        evidence=f"Found {match_count}/{len(keywords)} keywords. Missing: {missing}"
        if missing
        else f"All {len(keywords)} keywords found",
    )


def evaluate_structural_check(output: str, criterion: dict[str, Any]) -> CriterionResult:
    """Check structural properties of the output.

    Criterion format:
        checks: list of check dicts with:
            - type: "min_length" | "max_length" | "contains_section" |
                    "line_count_min" | "line_count_max" | "regex_match"
            - value: the threshold or pattern
    """
    checks = criterion.get("checks", [])
    passed = 0

    evidence_parts = []
    for check in checks:
        check_type = check["type"]
        value = check["value"]

        if check_type == "min_length":
            ok = len(output) >= value
            evidence_parts.append(
                f"min_length({value}): {'PASS' if ok else f'FAIL (got {len(output)})'}"
            )
        elif check_type == "max_length":
            ok = len(output) <= value
            evidence_parts.append(
                f"max_length({value}): {'PASS' if ok else f'FAIL (got {len(output)})'}"
            )
        elif check_type == "contains_section":
            ok = bool(re.search(rf"(?:^|\n)#{{1,3}}\s*.*{re.escape(value)}", output, re.IGNORECASE))
            evidence_parts.append(f"contains_section({value}): {'PASS' if ok else 'FAIL'}")
        elif check_type == "line_count_min":
            lines = len(output.strip().splitlines())
            ok = lines >= value
            evidence_parts.append(
                f"line_count_min({value}): {'PASS' if ok else f'FAIL (got {lines})'}"
            )
        elif check_type == "line_count_max":
            lines = len(output.strip().splitlines())
            ok = lines <= value
            evidence_parts.append(
                f"line_count_max({value}): {'PASS' if ok else f'FAIL (got {lines})'}"
            )
        elif check_type == "regex_match":
            ok = bool(re.search(value, output, re.IGNORECASE | re.MULTILINE))
            evidence_parts.append(f"regex_match({value}): {'PASS' if ok else 'FAIL'}")
        elif check_type == "not_contains":
            ok = value.lower() not in output.lower()
            evidence_parts.append(f"not_contains({value}): {'PASS' if ok else 'FAIL'}")
        else:
            ok = False
            evidence_parts.append(f"unknown_check({check_type}): SKIP")

        if ok:
            passed += 1

    score = passed / max(len(checks), 1)
    return CriterionResult(
        name=criterion["criterion"],
        criterion_type="structural_check",
        weight=criterion["weight"],
        score=score,
        evidence="; ".join(evidence_parts),
    )


def evaluate_factual_accuracy(output: str, criterion: dict[str, Any]) -> CriterionResult:
    """Check that output doesn't fabricate facts.

    Criterion format:
        allowed_facts: list of strings that may appear (from resume/job)
        forbidden_patterns: list of regex patterns that should NOT appear
    """
    forbidden = criterion.get("forbidden_patterns", [])
    violations = []

    for pattern in forbidden:
        if re.search(pattern, output, re.IGNORECASE):
            violations.append(pattern)

    # Also check for obvious fabrication signals
    fabrication_signals = [
        r"\b(?:I (?:have|had) (?:over )?\d{2,}\+? years)\b",  # Inflated years
    ]
    for signal in fabrication_signals:
        if re.search(signal, output, re.IGNORECASE):
            violations.append(f"fabrication_signal: {signal}")

    score = 1.0 if not violations else max(0.0, 1.0 - len(violations) * 0.25)

    return CriterionResult(
        name=criterion["criterion"],
        criterion_type="factual_accuracy",
        weight=criterion["weight"],
        score=score,
        evidence=f"Violations: {violations}" if violations else "No fabrication detected",
    )


async def evaluate_subjective_quality(
    output: str,
    criterion: dict[str, Any],
    judge_provider: Any | None = None,
) -> CriterionResult:
    """Use LLM-as-judge for subjective quality assessment.

    Falls back to heuristic scoring if no judge provider is available.

    Criterion format:
        description: what to evaluate
        scoring_guide: how to score (for the judge)
    """
    description = criterion.get("description", criterion["criterion"])
    scoring_guide = criterion.get(
        "scoring_guide",
        "Score 0-100 based on overall quality.",
    )

    if judge_provider is not None:
        try:
            from anvilcv.ai.provider import GenerationRequest, TaskType

            system_prompt = (
                "You are an expert evaluator scoring AI-generated content. "
                "Return ONLY a JSON object with 'score' (0-100 integer) and "
                "'reasoning' (1-2 sentences). No other text."
            )
            user_prompt = (
                f"Evaluate the following output on this criterion:\n\n"
                f"CRITERION: {description}\n"
                f"SCORING GUIDE: {scoring_guide}\n\n"
                f"OUTPUT TO EVALUATE:\n{output[:3000]}\n\n"
                f'Return JSON: {{"score": <0-100>, "reasoning": "..."}}'
            )

            request = GenerationRequest(
                task=TaskType.KEYWORD_EXTRACTION,  # Reuse existing task type
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
            )
            response = await judge_provider.generate(request)

            import json

            try:
                result = json.loads(response.content)
                judge_score = float(result["score"]) / 100.0
                reasoning = result.get("reasoning", "")
            except (json.JSONDecodeError, KeyError, ValueError):
                # Try to extract score from text
                match = re.search(r'"score"\s*:\s*(\d+)', response.content)
                if match:
                    judge_score = float(match.group(1)) / 100.0
                    reasoning = "Score extracted from partial JSON"
                else:
                    judge_score = 0.5
                    reasoning = "Could not parse judge response"

            return CriterionResult(
                name=criterion["criterion"],
                criterion_type="subjective_quality",
                weight=criterion["weight"],
                score=judge_score,
                evidence=f"LLM judge: {reasoning}",
            )
        except Exception as e:
            logger.warning("LLM judge failed, falling back to heuristics: %s", e)

    # Heuristic fallback: basic quality signals
    score = 0.5  # Baseline
    evidence_parts = []

    # Length heuristic: not too short, not empty
    if len(output.strip()) > 200:
        score += 0.1
        evidence_parts.append("adequate length")
    if len(output.strip()) > 500:
        score += 0.1
        evidence_parts.append("good length")

    # Structure heuristic: has paragraphs or sections
    if output.count("\n\n") >= 2:
        score += 0.1
        evidence_parts.append("has structure")

    # Specificity heuristic: contains numbers/metrics
    if re.search(r"\d+[%+KMB]|\d+,\d+|\d+\.\d+", output):
        score += 0.1
        evidence_parts.append("contains metrics")

    score = min(score, 1.0)

    return CriterionResult(
        name=criterion["criterion"],
        criterion_type="subjective_quality",
        weight=criterion["weight"],
        score=score,
        evidence=(
            f"Heuristic: {', '.join(evidence_parts)}" if evidence_parts else "Heuristic baseline"
        ),
    )


async def evaluate_output(
    output: str,
    rubric: list[dict[str, Any]],
    case_name: str,
    feature: str,
    provider: str,
    judge_provider: Any | None = None,
) -> EvaluationResult:
    """Evaluate AI output against a rubric, returning a scored result.

    Args:
        output: The AI-generated text to evaluate.
        rubric: List of criterion dicts from expected_rubric.yaml.
        case_name: Name of the test case (e.g., "case_01_sre").
        feature: Feature name (tailor, cover, prep).
        provider: Provider name used to generate the output.
        judge_provider: Optional AIProvider for subjective scoring.

    Returns:
        EvaluationResult with total score (0-100) and per-criterion details.
    """
    results: list[CriterionResult] = []

    for criterion in rubric:
        ctype = criterion.get("type", "keyword_presence")

        if ctype == "keyword_presence":
            result = evaluate_keyword_presence(output, criterion)
        elif ctype == "structural_check":
            result = evaluate_structural_check(output, criterion)
        elif ctype == "factual_accuracy":
            result = evaluate_factual_accuracy(output, criterion)
        elif ctype == "subjective_quality":
            result = await evaluate_subjective_quality(output, criterion, judge_provider)
        else:
            logger.warning("Unknown criterion type: %s", ctype)
            continue

        results.append(result)

    # Compute weighted total score (0-100)
    total_weight = sum(r.weight for r in results)
    if total_weight > 0:
        total_score = sum(r.score * r.weight for r in results) / total_weight * 100
    else:
        total_score = 0.0

    return EvaluationResult(
        case_name=case_name,
        feature=feature,
        provider=provider,
        total_score=total_score,
        criterion_results=results,
        raw_output=output,
    )


def evaluate_output_sync(
    output: str,
    rubric: list[dict[str, Any]],
    case_name: str,
    feature: str,
    provider: str,
    judge_provider: Any | None = None,
) -> EvaluationResult:
    """Synchronous wrapper for evaluate_output."""
    return asyncio.run(
        evaluate_output(output, rubric, case_name, feature, provider, judge_provider)
    )
