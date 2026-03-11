# Spec Self-Review Changelog

All issues found during the 3-pass self-review, organized by pass and risk domain.

## Pass 1 — Structural Review

| ID | Issue | Risk Domain | Fix Applied | File |
|----|-------|------------|-------------|------|
| S1 | `.anvil/debug/` directory referenced in AI provider fallback but missing from file system layout | R7 (External API) | Added `debug/` directory to file system layout with example file | `data-model.md` |
| S2 | `skills_taxonomy.yaml` mentioned in ATS scoring but structure not specified — a build agent would have to guess the format | R5 (ATS Honesty), R8 (Duplicate Implementation) | Added full example YAML structure for the taxonomy, including categories (languages, cloud, tools, certifications) with name/alias format. Added agent instruction that taxonomy is the ONLY source of keyword aliases. | `ats-scoring-model.md` |
| S3 | `anvil export` command defined in CLI interface but missing from feature tracker — no ID, priority, or success criteria | R4 (Composition Gaps) | Added F-ANV-17 (rendercv Export) as Core, P1, with testable success criteria | `feature-tracker.md` |
| S4 | Entry types in module inventory were incomplete — `one_line.py`, `publication.py`, `text.py` not listed despite being visible in rendercv's docs | R8 (Duplicate Implementation) | Added all missing entry types to the module inventory, all marked Untouched | `architecture.md` |

## Pass 2 — Semantic Review

| ID | Issue | Risk Domain | Fix Applied | File |
|----|-------|------------|-------------|------|
| M1 | Theme success criteria "distinct visual identity" is subjective and untestable by a build agent | — | Replaced with testable criteria: unique Pydantic design model, valid output for all entry types, snapshot tests pass | `feature-tracker.md` |
| M2 | Installation recommendation (`anvilcv[full]`) not documented — users and agents might install minimal package and wonder why CLI/rendering doesn't work | — | Added Prerequisites section to CLI docs specifying `pip install "anvilcv[full]"` as recommended, with explanation of minimal vs. full install | `cli-interface.md` |
| M3 | `anvil scan` with zero repos or zero matching repos not handled — would produce confusing empty output | R7 (External API) | Added two edge cases to scan error handling: zero public repos (exit 0 with message) and repos exist but none match filters (exit 0 with filter explanation) | `cli-interface.md` |
| M4 | Python version requirement (3.12+) not explicit in CLI docs or success criteria | — | Added Python 3.12+ to CLI prerequisites. Updated packaging success criteria to specify Python 3.12, 3.13, and 3.14 support. | `cli-interface.md`, `success-criteria.md` |

## Pass 3 — Adversarial Review

| ID | Issue | Risk Domain | Fix Applied | File |
|----|-------|------------|-------------|------|
| A1 | No import path guidance — build agents might import from `rendercv` directly instead of `anvilcv.vendor.rendercv`, causing vendored modifications to be bypassed | R8 (Duplicate Implementation), R1 (Fork Drift) | Added "Import Path Convention" section with CORRECT/WRONG examples and explicit rule | `architecture.md` |
| A2 | No pre-implementation checklist — agents might modify Untouched files or reimplement existing rendercv functionality | R8 (Duplicate Implementation), R1 (Fork Drift) | Added "Before Writing Code — Build Agent Checklist" with 5 mandatory steps | `architecture.md` |
| A3 | PDF text extraction failure not in score error handling — scorer would crash on scanned/image PDFs | R5 (ATS Honesty) | Added two cases: extraction fails completely (exit 1 with suggestion to use HTML) and partial extraction (warning with continuation) | `cli-interface.md` |
| A4 | Tier 2 golden-set tests described as "nightly" could be interpreted as optional — agents might mark AI features complete with only Tier 1 structural tests | R3 (LLM Non-Determinism) | Made Tier 2 explicitly mandatory for feature completion: "may not be marked as complete until it passes Tier 2" with specific score threshold (≥50/100) on all cases and all providers | `testing-strategy.md` |
| A5 | No enforcement mechanism for "Untouched" module protection — the spec says "MUST consult inventory" but nothing prevents violations | R1 (Fork Drift), R8 (Duplicate Implementation) | Added "Fork Integrity Check" CI script that compares all Untouched files against the v2.7 baseline. Any diff fails CI with an actionable error message. | `testing-strategy.md` |

## Open Question Resolution (Post-Review)

All 8 open questions resolved and implemented into spec files:

| OQ | Decision | Files Updated |
|----|----------|---------------|
| OQ-1 | `pdfminer.six` for PDF text extraction | `ats-scoring-model.md` |
| OQ-2 | Multi-source job input: URL (readability-lxml best-effort) + file + stdin (`--job -`) | `cli-interface.md`, `architecture.md`, `data-model.md` |
| OQ-3 | Vendor + patch files (definitive) | `architecture.md` |
| OQ-4 | `devforge` only for v1; terminal theme deferred post-v1 | `feature-tracker.md`, `architecture.md` |
| OQ-5 | Ollama tested set: llama3.1:8b + 70b; all others best-effort | `ai-provider-abstraction.md` |
| OQ-6 | Conditional requests (ETag) + caching + --max-repos 100 default | `cli-interface.md`, `architecture.md`, `feature-tracker.md` |
| OQ-7 | Markdown output for cover letter + prep; PDF rendering is P2 stretch | `cli-interface.md`, `feature-tracker.md`, `data-model.md` |
| OQ-8 | Static HTML deploy (responsive HTML + PDF link + CSS + meta tags, no JS) | `architecture.md`, `feature-tracker.md` |

## Summary

- **Pass 1 (Structural):** 4 issues found, 4 fixed
- **Pass 2 (Semantic):** 4 issues found, 4 fixed
- **Pass 3 (Adversarial):** 5 issues found, 5 fixed
- **Open Questions:** 8 resolved and implemented
- **Total:** 21 issues resolved

### Risk Domain Coverage

| Risk Domain | Issues Found | Resolution |
|------------|-------------|------------|
| R1 — Fork Upstream Drift | A1, A2, A5 | Import paths documented, agent checklist added, CI enforcement added |
| R2 — Provider Parity Illusion | (No new issues — addressed in initial draft via per-provider contracts) | — |
| R3 — LLM Output Non-Determinism | A4 | Tier 2 made mandatory for feature completion |
| R4 — Feature Composition Gaps | S3 | Missing feature (export) added to tracker |
| R5 — ATS Scoring Honesty | S2, A3 | Taxonomy structure documented, PDF failure handling added |
| R6 — Schema Migration Trap | (No new issues — addressed in initial draft via compatibility corpus) | — |
| R7 — External API Entanglement | S1, M3 | Debug directory added, zero-result edge cases handled |
| R8 — Duplicate Implementation | S2, S4, A1, A2, A5 | Taxonomy documented, entry types completed, import paths specified, checklist and CI enforcement added |
