# Testing Strategy

## Test Categories Overview

| Category | What It Tests | When It Runs | External Dependencies |
|----------|--------------|-------------|----------------------|
| Deterministic unit tests | Scoring logic, schema validation, CLI arg parsing, keyword extraction | Every CI run | None |
| Render pipeline tests | Full YAML → Typst/PDF/HTML/MD path | Every CI run | Typst binary (bundled) |
| Compatibility corpus | rendercv YAML round-trip identity | Every CI run | rendercv package (test dep) |
| LLM Tier 1 (structural) | AI output validates as YAML, conforms to schema | Every CI run | Mocked providers |
| LLM Tier 2 (golden-set) | AI output quality regression against reference pairs | Nightly + on-demand | Live provider APIs |
| LLM Tier 3 (human review) | Generated content quality for fixed test cases | Release gate | Human reviewers |
| Provider parity tests | Each AI feature works on each supported provider | Nightly + on-demand | Live provider APIs |
| Integration tests | GitHub API, job URL fetching, Vercel deployment | Nightly + on-demand | Live APIs or VCR recordings |

## 1. Deterministic Unit Tests

### Scope

- **ATS scoring rules** — Each rule in `scoring/rules/` has unit tests with known-good and known-bad inputs
- **Keyword extraction** — Skill taxonomy matching, alias resolution, deduplication
- **Section detection** — Header pattern matching for resume sections
- **Schema validation** — AnvilModel validation, variant model, job description model, GitHub profile model
- **CLI argument parsing** — Flag combinations, required args, error messages
- **Token budget calculator** — Budget allocation for different provider capabilities
- **Config resolution** — Provider selection, API key env var lookup

### Test Data

Test fixtures stored in `tests/fixtures/`:

```
tests/fixtures/
├── scoring/
│   ├── good_resume.txt          # Well-structured resume text
│   ├── bad_resume_multicol.txt  # Multi-column layout text
│   ├── bad_resume_no_dates.txt  # Missing dates
│   └── job_descriptions/
│       ├── sre_senior.txt       # Standard SRE job posting
│       ├── frontend_junior.txt  # Junior frontend role
│       └── ml_engineer.txt      # ML engineer role
├── schema/
│   ├── valid_anvil.yaml         # Valid Anvil YAML
│   ├── valid_rendercv.yaml      # Valid rendercv-only YAML
│   ├── invalid_extra_field.yaml # Unknown field in anvil section
│   └── invalid_provider.yaml    # Invalid provider config
└── keywords/
    ├── skills_input.txt         # Raw job description text
    └── skills_expected.yaml     # Expected extracted skills
```

### Execution

```bash
pytest tests/unit/ -x --numprocesses=auto
```

Every unit test must be:
- Deterministic (same input → same output, always)
- Fast (< 100ms each)
- Independent (no shared state, no file system side effects)

## 2. Render Pipeline Tests

### Scope

Integration tests for the full rendering pipeline:

- YAML → AnvilModel validation → Typst source → PDF
- YAML → AnvilModel validation → Markdown → HTML
- YAML → AnvilModel validation → ATS HTML
- Variant rendering (multiple YAML files)
- Theme rendering (all built-in + Anvil themes)

### Snapshot Testing

Rendered Typst and Markdown outputs are snapshot-tested:

```python
def test_render_devforge_theme(snapshot):
    model = build_model("tests/fixtures/rendering/devforge_sample.yaml")
    typst_output = generate_typst(model)
    assert typst_output == snapshot  # Snapshot stored in tests/snapshots/
```

Snapshots are updated explicitly: `pytest --snapshot-update`

### What's NOT Snapshot-Tested

- PDF files — binary output varies by Typst version and platform
- PNG files — derived from PDF, same variance
- ATS HTML — snapshot-tested on structure (DOM tree), not whitespace

## 3. Compatibility Corpus Tests

See [Migration & Compatibility](migration-compatibility.md) for corpus contents and comparison method.

These tests compare Anvil output against rendercv output for the same input. They run in CI on every push.

```python
@pytest.mark.parametrize("yaml_file", get_corpus_files())
def test_compatibility_typst(yaml_file):
    anvil_typst = render_with_anvil(yaml_file, format="typst")
    rendercv_typst = render_with_rendercv(yaml_file, format="typst")
    assert anvil_typst == rendercv_typst, f"Typst mismatch for {yaml_file}"

@pytest.mark.parametrize("yaml_file", get_corpus_files())
def test_compatibility_markdown(yaml_file):
    anvil_md = render_with_anvil(yaml_file, format="markdown")
    rendercv_md = render_with_rendercv(yaml_file, format="markdown")
    assert anvil_md == rendercv_md, f"Markdown mismatch for {yaml_file}"

@pytest.mark.parametrize("yaml_file", get_corpus_files())
def test_compatibility_html(yaml_file):
    anvil_html = render_with_anvil(yaml_file, format="html")
    rendercv_html = render_with_rendercv(yaml_file, format="html")
    assert anvil_html == rendercv_html, f"HTML mismatch for {yaml_file}"
```

## 4. LLM Output Evaluation (Tiered)

### Tier 1 — Structural Validation (Every CI Run)

AI provider calls are **mocked** in CI. Mock responses are stored as fixture files.

For each AI feature (tailor, prep, cover), Tier 1 tests verify:

1. **Output parses as valid YAML** — `yaml.safe_load()` succeeds
2. **Output conforms to schema** — Pydantic model validation passes
3. **Required sections present** — All expected fields exist
4. **No hallucinated fields** — No fields outside the schema
5. **Provenance metadata complete** — Source, job, timestamp, provider fields present

```python
def test_tailor_output_structure(mock_anthropic):
    mock_anthropic.return_value = load_fixture("tailor_response_anthropic.yaml")
    result = tailor_resume(source_yaml, job_description, provider="anthropic")

    # Structural checks
    assert isinstance(result, dict)
    assert "cv" in result
    assert "anvil" in result
    assert "variant" in result["anvil"]
    assert result["anvil"]["variant"]["source"] is not None
    assert result["anvil"]["variant"]["created_at"] is not None

    # Schema validation
    AnvilModel.model_validate(result)  # Must not raise
```

**Tier 1 is NOT sufficient for feature completion.** An AI feature is considered "untested" and may not be marked as complete until it passes Tier 2 golden-set regression with a score ≥ 50/100 on ALL test cases for ALL supported providers. This is a release-blocking requirement, not a nice-to-have.

### Tier 2 — Golden-Set Regression (Nightly / On-Demand)

Each AI feature has 5-10 reference input/output pairs:

```
tests/golden/
├── tailor/
│   ├── case_01_sre/
│   │   ├── input_resume.yaml
│   │   ├── input_job.yaml
│   │   ├── expected_rubric.yaml   # Evaluation criteria
│   │   └── baseline_scores.yaml   # Historical scores
│   ├── case_02_frontend/
│   │   └── ...
│   └── case_03_ml_engineer/
│       └── ...
├── cover/
│   └── ...
└── prep/
    └── ...
```

Each golden-set case has a **rubric** — a set of criteria evaluated by LLM-as-judge:

```yaml
# expected_rubric.yaml
rubric:
  - criterion: "Bullets mention Kubernetes"
    weight: 0.3
    type: keyword_presence
  - criterion: "Project order changed (infra project first)"
    weight: 0.2
    type: structural_check
  - criterion: "No fabricated metrics"
    weight: 0.3
    type: factual_accuracy
  - criterion: "Tone matches job description formality"
    weight: 0.2
    type: subjective_quality
```

**Evaluation:** For objective criteria (keyword_presence, structural_check, factual_accuracy), use deterministic checks. For subjective criteria, use LLM-as-judge with a separate evaluator prompt.

**Scoring:** Each case produces a 0-100 score. Scores are tracked over time. A score drop > 15 points from the previous nightly run triggers an alert.

**Provider matrix:** Golden-set tests run against **each supported provider** independently. Provider-specific failures are reported separately, not aggregated.

### Tier 3 — Human Review (Release Gate)

Before each release:

1. Run all Tier 2 golden-set cases
2. Generate fresh output for 3 fixed test cases (one per AI feature: tailor, cover, prep)
3. Human reviewer evaluates output against rubric
4. All 3 cases must pass human review before release

Human review criteria:
- Factual accuracy (no fabricated achievements)
- Tone appropriateness
- Keyword alignment with job description
- Readability and coherence
- No artifacts or formatting errors

## 5. Mock Strategy

### What's Mocked in CI

| External API | Mocked? | Mock Method | Fixture Location |
|-------------|---------|-------------|-----------------|
| Anthropic API | Yes | `unittest.mock.patch` on provider `generate()` | `tests/fixtures/ai/anthropic/` |
| OpenAI API | Yes | `unittest.mock.patch` on provider `generate()` | `tests/fixtures/ai/openai/` |
| Ollama API | Yes | `unittest.mock.patch` on provider `generate()` | `tests/fixtures/ai/ollama/` |
| GitHub API | Yes | VCR cassettes (`vcrpy`) | `tests/fixtures/github/cassettes/` |
| Job URL fetching | Yes | `responses` library mock | `tests/fixtures/jobs/` |
| Vercel API | Yes | `unittest.mock.patch` | `tests/fixtures/deploy/` |
| Typst binary | **NOT mocked** | Bundled as dependency | N/A |

### What Needs Live Access

| Test Category | When | Requires |
|--------------|------|----------|
| Tier 2 golden-set | Nightly | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, Ollama running locally |
| Tier 3 human review | Pre-release | Same as Tier 2 + human reviewer |
| GitHub integration (live) | On-demand | `GITHUB_TOKEN` |
| Vercel deployment (live) | On-demand | `VERCEL_TOKEN` |

### Keeping Fixtures Fresh

Mock fixtures are regenerated:

- **AI fixtures:** Quarterly, or when prompts change. Run `python tests/update_ai_fixtures.py` with live API keys.
- **GitHub cassettes:** Quarterly, or when GitHub API version changes. Run `pytest tests/integration/github/ --vcr-record=new_episodes`.
- **Job URL fixtures:** As needed when job parsing logic changes.

## 6. Provider Parity Tests

Each AI feature has at least one test that runs against each supported provider:

```python
@pytest.mark.parametrize("provider", ["anthropic", "openai", "ollama"])
@pytest.mark.nightly
def test_tailor_provider_parity(provider, golden_case_01):
    """Each provider must produce structurally valid tailored output."""
    result = tailor_resume(
        golden_case_01.input_resume,
        golden_case_01.input_job,
        provider=provider,
    )
    # Structural validation (same as Tier 1)
    AnvilModel.model_validate(result)

    # Quality evaluation (Tier 2 rubric)
    score = evaluate_against_rubric(result, golden_case_01.rubric)
    assert score >= 50, f"Provider {provider} scored {score}/100 (minimum: 50)"

    # Log score for tracking
    log_provider_score(provider, "tailor", "case_01", score)
```

Provider-specific failures are visible in test results — not hidden behind the abstraction. If Ollama fails but Anthropic passes, the report shows this clearly.

## Test Directory Structure

```
tests/
├── unit/
│   ├── scoring/          # ATS scoring rules
│   ├── schema/           # Model validation
│   ├── cli/              # CLI argument parsing
│   ├── ai/               # Token budget, output parsing
│   ├── github/           # Metric extraction
│   └── tailoring/        # Keyword matching, variant writing
├── integration/
│   ├── rendering/        # Full render pipeline
│   ├── github/           # GitHub API (VCR)
│   └── deploy/           # Vercel deployment
├── corpus/               # Compatibility corpus YAML files
├── golden/               # Golden-set test cases for AI features
├── fixtures/             # Mock data and test inputs
├── snapshots/            # Snapshot test references
└── conftest.py           # Shared fixtures and markers
```

## Fork Integrity Check

A CI check verifies that modules marked **Untouched** in the architecture spec have not been modified from the vendored baseline:

```bash
# scripts/check_untouched_modules.sh
# Compares vendored files against the rendercv v2.7 baseline
# Any diff in an Untouched file fails CI

UNTOUCHED_FILES=(
  "vendor/rendercv/exception.py"
  "vendor/rendercv/cli/copy_templates.py"
  "vendor/rendercv/cli/render_command/progress_panel.py"
  "vendor/rendercv/cli/render_command/parse_override_arguments.py"
  "vendor/rendercv/cli/render_command/watcher.py"
  "vendor/rendercv/schema/pydantic_error_handling.py"
  "vendor/rendercv/schema/override_dictionary.py"
  "vendor/rendercv/schema/variant_pydantic_model_generator.py"
  "vendor/rendercv/schema/models/base.py"
  "vendor/rendercv/schema/models/path.py"
  "vendor/rendercv/schema/models/validation_context.py"
  "vendor/rendercv/schema/models/custom_error_types.py"
  "vendor/rendercv/schema/models/cv/"
  "vendor/rendercv/schema/models/design/built_in_design.py"
  "vendor/rendercv/schema/models/design/classic_theme.py"
  "vendor/rendercv/schema/models/design/color.py"
  "vendor/rendercv/schema/models/design/font_family.py"
  "vendor/rendercv/schema/models/design/other_themes/"
  "vendor/rendercv/schema/models/locale/"
  "vendor/rendercv/schema/models/settings/"
  "vendor/rendercv/renderer/typst.py"
  "vendor/rendercv/renderer/pdf_png.py"
  "vendor/rendercv/renderer/markdown.py"
  "vendor/rendercv/renderer/templater/model_processor.py"
  "vendor/rendercv/renderer/templater/entry_templates_from_input.py"
  "vendor/rendercv/renderer/templater/connections.py"
  "vendor/rendercv/renderer/templater/date.py"
  "vendor/rendercv/renderer/templater/string_processor.py"
  "vendor/rendercv/renderer/templater/markdown_parser.py"
)

for file in "${UNTOUCHED_FILES[@]}"; do
  if ! diff -q "src/anvilcv/$file" "baseline/rendercv-v2.7/$file" > /dev/null 2>&1; then
    echo "ERROR: Untouched module modified: $file"
    echo "This file is marked Untouched in the architecture spec."
    echo "Do not modify it. Create a wrapper or extension instead."
    exit 1
  fi
done
echo "All untouched modules intact."
```

This check runs on every CI push and prevents accidental modification of vendored modules.

## CI Configuration

```yaml
# .github/workflows/test.yaml
jobs:
  unit-and-integration:
    # Runs on every push
    steps:
      - run: pytest tests/unit/ tests/integration/rendering/ tests/corpus/ -x --numprocesses=auto
    # Uses only mocked dependencies

  nightly-ai:
    # Runs nightly and on-demand
    schedule:
      - cron: "0 3 * * *"
    steps:
      - run: pytest tests/golden/ -m "nightly" --numprocesses=1
    # Requires: ANTHROPIC_API_KEY, OPENAI_API_KEY, Ollama
    # Sequential (--numprocesses=1) to avoid rate limits
```
