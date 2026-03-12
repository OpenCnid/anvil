# Composition Pipelines

## Design Philosophy

Anvil commands are composable stages that communicate via files on disk (Principle P8). Each command reads files, writes files, and exits. Intermediate files are the integration contract.

Canonical pipelines are the tested, documented multi-command workflows. Users can compose freely beyond these, but only canonical pipelines have integration test coverage.

## Canonical Pipeline 1: GitHub Scan → Tailor → Render

**Use case:** "I have a GitHub profile and a job I want to apply for. Give me a tailored resume from scratch."

### Steps

```bash
# Step 1: Scan GitHub for project data
anvil scan --github janedeveloper --merge Jane_Developer_CV.yaml

# Step 2: Tailor for a specific job
anvil tailor Jane_Developer_CV.yaml --job https://acme.com/careers/sre

# Step 3: Render the tailored variant
anvil render variants/Jane_Developer_Acme_SRE_2026-03-10.yaml
```

### Data Flow

```
Step 1: GitHub API → .anvil/github/janedeveloper.yaml
        .anvil/github/janedeveloper.yaml + Jane_Developer_CV.yaml
          → Jane_Developer_CV_with_github.yaml (new file, not overwrite)

Step 2: Jane_Developer_CV.yaml + job URL
          → .anvil/jobs/acme-sre-2026-03.yaml (parsed job description)
          → variants/Jane_Developer_Acme_SRE_2026-03-10.yaml (tailored variant)

Step 3: variants/Jane_Developer_Acme_SRE_2026-03-10.yaml
          → output/Jane_Developer_Acme_SRE_2026-03-10.pdf
          → output/Jane_Developer_Acme_SRE_2026-03-10.typ
          → output/Jane_Developer_Acme_SRE_2026-03-10.md
          → output/Jane_Developer_Acme_SRE_2026-03-10.html
          → output/Jane_Developer_Acme_SRE_2026-03-10_ats.html
          → output/Jane_Developer_Acme_SRE_2026-03-10_1.png
```

### Failure Handling

| Stage | Failure | Result |
|-------|---------|--------|
| Step 1 (scan) | GitHub API rate limit | Partial scan results written to `.anvil/github/`. User can retry or proceed with existing data. Step 2 works without GitHub data. |
| Step 1 (scan) | No GitHub token | Warning printed. Unauthenticated scan with 60 req/hr limit. May be incomplete. |
| Step 2 (tailor) | Job URL unreachable | Error. User can save job description manually and pass as file: `--job ./jobs/acme-sre.yaml` |
| Step 2 (tailor) | AI provider error | Error. No variant file written. User can retry with different provider. |
| Step 3 (render) | Typst rendering error | Error. YAML file exists but PDF is not generated. Error message includes Typst diagnostics. |

## Canonical Pipeline 2: Tailor → Score → Render

**Use case:** "I want to tailor my resume for a job, check ATS compatibility, then render."

### Steps

```bash
# Step 1: Tailor for job
anvil tailor Jane_Developer_CV.yaml --job https://acme.com/careers/sre

# Step 2: Score the tailored variant
anvil score variants/Jane_Developer_Acme_SRE_2026-03-10.yaml --job .anvil/jobs/acme-sre-2026-03.yaml

# Step 3: (If score is acceptable) Render
anvil render variants/Jane_Developer_Acme_SRE_2026-03-10.yaml
```

### Shortcut: Combined Flags

```bash
# All three steps in one command
anvil tailor Jane_Developer_CV.yaml --job https://acme.com/careers/sre --score --render
```

When `--score` is passed to `anvil tailor`:
1. Tailor generates variant YAML
2. Variant is rendered to temporary output
3. Score is run on rendered output against the same job description
4. Score report is printed to terminal
5. If `--render` is also passed, final output files are written

### Data Flow

```
Step 1: Jane_Developer_CV.yaml + job URL
          → .anvil/jobs/acme-sre-2026-03.yaml
          → variants/Jane_Developer_Acme_SRE_2026-03-10.yaml

Step 2: variants/Jane_Developer_Acme_SRE_2026-03-10.yaml (rendered internally)
          → Score report (terminal + optional YAML file)

Step 3: variants/Jane_Developer_Acme_SRE_2026-03-10.yaml
          → output/ (PDF, Typst, MD, HTML, ATS HTML, PNG)
```

### Failure Handling

| Stage | Failure | Result |
|-------|---------|--------|
| Step 1 (tailor) | AI error | Error. No variant written. Pipeline stops. |
| Step 2 (score) | Rendering error during scoring | Score report incomplete. Parsability checks may still produce results. |
| Step 3 (render) | Typst error | Error. Score report from step 2 is still available. |
| Combined (`--score --render`) | Score fails | Render still proceeds. Score failure is a warning, not a blocker. |

## Canonical Pipeline 3: Full Pipeline (Scan → Tailor → Score → Render → Deploy)

**Use case:** "Full automation — scan GitHub, tailor for job, check ATS, render, deploy."

### Steps

```bash
# Full manual pipeline
anvil scan --github janedeveloper
anvil tailor Jane_Developer_CV.yaml --job https://acme.com/careers/sre --score --render
anvil deploy variants/Jane_Developer_Acme_SRE_2026-03-10.yaml
```

### No Single-Command Pipeline

There is no `anvil pipeline` command in v1. The full pipeline is composed from individual commands. Rationale:

1. Each step has different failure modes requiring different user responses
2. Users need to inspect intermediate output (e.g., review tailored YAML before rendering)
3. A monolithic pipeline command hides complexity and makes debugging harder
4. The `--score --render` shortcut on `tailor` covers the most common composition

### Failure Handling

Each step is independent. Failure at any step produces partial results on disk. Users can fix the issue and resume from the failed step. No step cleans up output from previous steps.

## Intermediate File Formats

| Between Steps | File Format | Location |
|--------------|-------------|----------|
| scan → tailor | GitHub profile YAML | `.anvil/github/{username}.yaml` |
| tailor → score | Tailored variant YAML + rendered output | `variants/` + temp render |
| tailor → render | Tailored variant YAML | `variants/` |
| score → (user decision) | Score report YAML | terminal or file |
| render → deploy | Rendered HTML | `output/` |

All intermediate files are human-readable YAML or Markdown. Users can inspect, edit, and re-run any step.

## Non-Canonical Compositions

Users may compose commands in any order. Some useful but untested compositions:

| Composition | Use Case | Notes |
|-------------|----------|-------|
| `score → tailor` | Score first, then tailor to fix issues | User manually addresses score feedback in tailoring prompt |
| `scan → render` (no tailor) | Render with GitHub data, no job-specific tailoring | Works — scan merges data into YAML, render produces output |
| `cover → prep` | Generate cover letter, then prep notes from the same job | Both read the same job YAML independently |
| `tailor → tailor` | Re-tailor a variant for a different job | Works — variant YAML is valid Anvil YAML |

Non-canonical compositions may produce unexpected results (e.g., tailoring a variant that's already tailored may over-optimize). Anvil does not prevent this but logs a warning when the input YAML already contains variant provenance metadata.
