# Design Principles

These are non-negotiable. When two valid approaches conflict, these principles resolve the ambiguity. They are ordered by priority — earlier principles override later ones.

## P1 — YAML Is the Source of Truth

Never mutate the user's input file. Tailored variants are always new files. AI-generated content is always written to a separate YAML file with a clear provenance chain back to the source. The user's original resume YAML is read-only to every Anvil operation.

**Resolves:** Any temptation to "helpfully" edit the user's file during tailoring, scoring, or scanning.

## P2 — Offline-First, Keys-Optional

Core features (render, score, new themes, multi-variant) work with zero configuration — no API keys, no tokens, no internet connection, no accounts. Extended features (AI tailoring, GitHub scan, cover letter, interview prep, deploy) require user-provided API keys and degrade gracefully without them. "Gracefully" means: a clear error message explaining exactly what key is needed and how to set it, never a stack trace, never silent failure, never a truncated output with no explanation.

**Resolves (R2, R7):** The boundary between "works out of the box" and "needs configuration" must be unambiguous. Every CLI command is classified as Core or Extended. A user who never sets an API key should never encounter an error about missing keys.

## P3 — Fork-Aware, Not Fork-Hostile

Anvil is a hard fork, not a wrapper. But it's a *respectful* fork. Every rendercv module is classified as Untouched (use as-is), Extended (add to, don't break), or Modified (changed internals, track upstream drift). The module inventory in the architecture spec is the canonical reference. Build agents MUST consult the inventory before modifying any file in the rendercv vendor tree.

**Resolves (R1, R8):** Prevents agents from reimplementing existing rendercv functionality. Prevents accidental modification of modules marked "untouched." Makes upstream merge evaluation tractable.

## P4 — Forward-Compatible, One Direction

Anvil reads any valid rendercv YAML file and renders it identically to rendercv. rendercv cannot read Anvil YAML (Anvil adds fields rendercv doesn't recognize). This is a one-way contract. Every mention of "compatible" in this spec means Anvil-reads-rendercv, never the reverse.

**Resolves (R6):** The compatibility direction. Anvil's validator must not reject YAML that rendercv accepts. Anvil's extended fields are additive — they use rendercv's `BaseModelWithoutExtraKeys` pattern for Anvil-specific sections, not by modifying rendercv's core models.

## P5 — Providers Are Not Fungible

Anthropic Claude, OpenAI GPT, and Ollama local models have different context windows (8K to 200K), different structured output methods (JSON mode, XML parsing, freeform), different rate limits, and different prompting requirements. The provider abstraction makes them *pluggable*, not *interchangeable*. Each provider has a documented capability contract. Prompts are per-provider, not universal. Test suites run against each provider independently.

**Resolves (R2):** Prevents the "works on Claude, breaks on Ollama" failure mode. Forces explicit handling of provider differences rather than assuming fungibility.

## P6 — Honest Claims, Bounded Confidence

The ATS score checker is a heuristic keyword and structure analyzer. It is not an ATS simulator. It cannot replicate the proprietary parsing of Greenhouse, Lever, or Workday. Every scoring rule is classified as "evidence-based" (cites research or reverse-engineering source) or "opinionated heuristic" (best-practice recommendation without ground truth). The UI communicates this distinction to users.

**Resolves (R5):** Prevents users from over-trusting scores. Prevents build agents from inventing plausible-sounding scoring rules with no evidence.

## P7 — Deterministic by Default, AI by Choice

Every Anvil operation that doesn't explicitly invoke an LLM produces identical output for identical input. AI features are opt-in, clearly marked, and their non-deterministic nature is documented. Testing strategies differ between deterministic and AI-powered features (see Testing Strategy spec).

**Resolves (R3):** Sets expectations for testing. Deterministic code gets snapshot tests. AI code gets structural validation + golden-set regression + human review.

## P8 — Composition Over Monolith

Anvil commands are composable stages that communicate via files on disk. `scan` writes YAML. `tailor` reads YAML and writes YAML. `score` reads rendered output and writes a report. `render` reads YAML and writes PDF/HTML/etc. Canonical pipelines are documented, but users can compose freely. Intermediate files are the integration contract — not in-memory state.

**Resolves (R4):** Makes feature composition explicit. Each command's input and output formats are documented. Pipeline failures produce partial output that users can inspect and resume from.

## P9 — Errors Are User-Facing, Not Developer-Facing

Every error message tells the user: (1) what went wrong, (2) why it matters, and (3) what to do about it. No stack traces in normal operation. No error codes without explanations. No "An error occurred" without specifics. Extended features that fail due to missing credentials include the exact environment variable name and a link to setup instructions.

**Resolves:** The gap between developer-comprehensible errors and user-comprehensible errors. Follows rendercv's existing pattern of human-readable validation errors.

## P10 — English-First for v1 AI, i18n-Preserved for Rendering

AI features (tailoring, cover letter, interview prep) target English-language resumes and job descriptions in v1. Non-English input is accepted but AI output quality is not guaranteed or tested. rendercv's existing i18n/locale support for date formatting and section headers is fully preserved and not modified.

**Resolves:** Scope boundary for AI language support without breaking existing locale features.
