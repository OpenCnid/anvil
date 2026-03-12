# CLI Interface

## Prerequisites

- **Python 3.12+** required (inherits from rendercv)
- **Recommended install:** `pip install "anvilcv[full]"` — includes Typst binary, CLI (Typer), watch mode, and fonts
- **Minimal install:** `pip install anvilcv` — core library only (YAML parsing, validation, scoring). No CLI, no rendering. Useful for programmatic use.

## Global Options

```
anvil [OPTIONS] COMMAND [ARGS]

Options:
  -v, --version   Show Anvil version and exit
  -h, --help      Show help and exit
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (invalid YAML, missing file, validation failure) |
| 2 | CLI usage error (invalid flags, missing arguments) |
| 3 | External service error (API failure, network timeout) |
| 4 | AI provider error (missing key, rate limit, malformed response) |

---

## `anvil render`

Render a YAML file into PDF, Typst, Markdown, HTML, PNG, and ATS HTML.

Identical to `rendercv render` for rendercv-compatible YAML, plus:
- Produces ATS-optimized HTML output (`_ats.html`)
- Supports `--variant` for batch variant rendering

```
anvil render INPUT_FILE [OPTIONS]

Arguments:
  INPUT_FILE    Path to YAML file (required)

Options:
  --output-dir, -o PATH      Output directory (default: ./output/)
  --design PATH               Overlay design YAML file
  --locale PATH               Overlay locale YAML file
  --settings PATH              Overlay settings YAML file
  --watch, -w                  Watch for changes and re-render
  --variant PATH               Render all YAML files in a variant directory
  --no-ats-html                Skip ATS HTML generation
  --override KEY=VALUE         Override YAML values (repeatable)
  -h, --help                   Show help
```

**Examples:**

```bash
# Basic render (identical to rendercv)
anvil render John_Doe_CV.yaml

# Render with output directory
anvil render John_Doe_CV.yaml -o ./build/

# Watch mode
anvil render John_Doe_CV.yaml --watch

# Render all variants
anvil render John_Doe_CV.yaml --variant ./variants/

# Override theme on the fly
anvil render John_Doe_CV.yaml --override design.theme=devforge
```

**Error behavior:**

| Condition | Behavior |
|-----------|----------|
| YAML file not found | Exit 1: "File not found: {path}" |
| YAML validation fails | Exit 1: Detailed validation errors (same format as rendercv) |
| Typst rendering fails | Exit 1: Typst error message with line reference |
| Variant directory empty | Exit 1: "No YAML files found in {path}" |

---

## `anvil new`

Create a new resume YAML file with Anvil-extended schema.

```
anvil new FULL_NAME [OPTIONS]

Arguments:
  FULL_NAME     Full name for the resume (required)

Options:
  --theme THEME              Theme to use (default: devforge)
  --rendercv-compat          Generate rendercv-compatible YAML (no anvil section)
  -h, --help                 Show help
```

**Examples:**

```bash
# Create new Anvil-flavored YAML
anvil new "Jane Developer"

# Create rendercv-compatible YAML
anvil new "Jane Developer" --rendercv-compat

# Create with specific theme
anvil new "Jane Developer" --theme terminal
```

---

## `anvil score`

Run ATS heuristic analysis on a rendered resume.

**Classification: Core** — No API keys required. Keyword extraction uses heuristic parsing by default.

```
anvil score INPUT [OPTIONS]

Arguments:
  INPUT         Path to rendered PDF, HTML, or YAML file (required).
                If YAML is provided, Anvil renders it first, then scores the output.

Options:
  --job, -j PATH_OR_URL_OR_STDIN  Job description file, URL (best-effort heuristic parsing via readability-lxml), or `-` for stdin
  --format FORMAT            Output format: terminal (default), yaml, json
  --output, -o PATH          Write report to file (default: terminal only)
  --verbose                  Show individual rule details
  -h, --help                 Show help
```

**Examples:**

```bash
# Score a rendered PDF
anvil score ./output/Jane_Developer_CV.pdf

# Score against a job description URL (best-effort heuristic parsing)
anvil score ./output/Jane_Developer_CV.pdf --job https://acme.com/careers/sre

# Score against a local job description file
anvil score Jane_Developer_CV.yaml --job ./jobs/acme-sre.yaml

# Score with job description from stdin (e.g., pasted text)
cat job_description.txt | anvil score Jane_Developer_CV.yaml --job -

# Output as YAML for programmatic use
anvil score Jane_Developer_CV.yaml --format yaml -o score_report.yaml
```

**Error behavior:**

| Condition | Behavior |
|-----------|----------|
| Input file not found | Exit 1: "File not found: {path}" |
| Unsupported input format | Exit 1: "Unsupported format. Provide a .pdf, .html, or .yaml file" |
| PDF text extraction fails | Exit 1: "Could not extract text from {path}. The PDF may be image-based (scanned) rather than machine-readable. Try scoring the HTML output instead: `anvil score output/resume.html`" |
| PDF text extraction is partial | Warning: "Text extraction from {path} may be incomplete. {n} pages extracted, {m} appear to be images. Score may be inaccurate." (Continues with available text) |
| Job URL unreachable | Exit 3: "Could not fetch job description from {url}: {reason}. Scoring without job keywords." (Continues with structure-only scoring) |
| Job URL returns non-HTML content | Exit 3: "Could not parse job description from {url}. Expected HTML, got {content_type}. Save the job description as a text file and use `--job ./path/to/job.txt` instead." |
| Job URL returns SPA/JS-rendered content | Warning: "Page at {url} may require JavaScript rendering. Extracted content may be incomplete. If results look wrong, save the job description text to a file: `--job ./path/to/job.txt`" (Continues with whatever was extracted) |

---

## `anvil tailor`

Generate a tailored resume variant for a specific job description.

**Classification: Extended** — Requires AI provider API key.

```
anvil tailor INPUT_FILE [OPTIONS]

Arguments:
  INPUT_FILE    Path to source YAML file (required)

Options:
  --job, -j PATH_OR_URL_OR_STDIN  Job description file, URL (best-effort heuristic parsing), or `-` for stdin (required)
  --provider PROVIDER        AI provider: anthropic, openai, ollama (default: from config)
  --model MODEL              Override model name
  --output, -o PATH          Output path for tailored YAML (default: variants dir from config)
  --render                   Also render the tailored variant after generating
  --score                    Also score the tailored variant after rendering
  --dry-run                  Show what would change without writing files
  -h, --help                 Show help
```

**Examples:**

```bash
# Basic tailoring (URL — best-effort heuristic parsing)
anvil tailor Jane_Developer_CV.yaml --job https://acme.com/careers/sre

# Tailor + render + score in one command
anvil tailor Jane_Developer_CV.yaml --job https://acme.com/careers/sre --render --score

# Use specific provider
anvil tailor Jane_Developer_CV.yaml --job ./jobs/acme-sre.yaml --provider openai

# Dry run to preview changes
anvil tailor Jane_Developer_CV.yaml --job ./jobs/acme-sre.yaml --dry-run

# Use local model via Ollama
anvil tailor Jane_Developer_CV.yaml --job ./jobs/acme-sre.yaml --provider ollama --model llama3.1:70b

# Tailor from stdin (paste job description)
cat job_description.txt | anvil tailor Jane_Developer_CV.yaml --job -
```

**LLM failure behavior:**

| Condition | Behavior |
|-----------|----------|
| No provider configured and no `--provider` flag | Exit 4: "No AI provider configured. Set `anvil.providers.default` in your YAML or pass `--provider`. Supported providers: anthropic, openai, ollama. See https://docs.anvilcv.com/providers for setup." |
| API key env var not set | Exit 4: "API key not found. Set the {ENV_VAR} environment variable. See https://docs.anvilcv.com/providers/{provider} for setup." |
| API returns 429 (rate limit) | Exit 4: "Rate limited by {provider}. Retry after {retry_after} seconds. Consider using a different provider with `--provider`." |
| API returns 5xx | Exit 3: "Provider {provider} is experiencing issues ({status}). Try again later or use `--provider` to switch." |
| Response fails schema validation | Exit 4: "AI response was malformed. This can happen with smaller models. Try a larger model with `--model` or a different provider." The malformed response is logged to `.anvil/debug/` for inspection. |
| Job URL unreachable | Exit 3: "Could not fetch job description from {url}: {reason}" |

---

## `anvil scan`

Scan GitHub repos and generate project entries.

**Classification: Extended** — Requires GitHub token for useful rate limits.

```
anvil scan [OPTIONS]

Options:
  --github, -g USERNAME      GitHub username to scan (required, or set in config)
  --output, -o PATH          Output path for GitHub profile YAML (default: .anvil/github/)
  --merge INPUT_FILE         Merge generated entries into an existing YAML file (writes new file)
  --format FORMAT            Output format: yaml (default), entries-only
  --max-repos N              Maximum repos to scan (default: 100)
  --since DATE               Only repos with activity since DATE (YYYY-MM-DD)
  -h, --help                 Show help
```

**Examples:**

```bash
# Scan GitHub profile
anvil scan --github janedeveloper

# Scan and merge into existing resume
anvil scan --github janedeveloper --merge Jane_Developer_CV.yaml

# Scan recent activity only
anvil scan --github janedeveloper --since 2025-01-01
```

**Error behavior:**

| Condition | Behavior |
|-----------|----------|
| No GitHub token set | Warning: "No GitHub token found. Using unauthenticated API (60 requests/hour). Set {GITHUB_TOKEN} for 5000 requests/hour." (Continues with reduced rate limit) |
| GitHub API rate limited | Exit 3: "GitHub API rate limit reached. {remaining} requests used. Resets at {reset_time}. Set a GitHub token for higher limits." Partial results are written to disk. Re-running uses conditional requests (ETag/If-None-Match) — cached repos won't consume additional API calls. |
| Username not found | Exit 1: "GitHub user '{username}' not found." |
| User has zero public repos | Exit 0: "No public repositories found for '{username}'. Check the username or make repositories public." Writes empty profile YAML. |
| User has repos but none match filters | Exit 0: "Found {n} repos for '{username}' but none matched filters (min_commits={x}, exclude={list}). Adjust filters in your config." |

---

## `anvil prep`

Generate interview preparation notes.

**Classification: Extended** — Requires AI provider API key.

```
anvil prep INPUT_FILE [OPTIONS]

Arguments:
  INPUT_FILE    Path to resume YAML or variant file (required)

Options:
  --job, -j PATH_OR_URL_OR_STDIN  Job description file, URL (best-effort), or `-` for stdin (required)
  --provider PROVIDER        AI provider (default: from config)
  --output, -o PATH          Output path for prep notes (default: ./{name}_prep.md)
  -h, --help                 Show help
```

**Examples:**

```bash
# Generate prep notes
anvil prep Jane_Developer_CV.yaml --job https://acme.com/careers/sre

# Prep from a tailored variant
anvil prep variants/Jane_Developer_Acme_SRE.yaml --job .anvil/jobs/acme-sre.yaml
```

**LLM failure behavior:** Same as `anvil tailor` (see table above).

---

## `anvil cover`

Generate a cover letter.

**Classification: Extended** — Requires AI provider API key.

```
anvil cover INPUT_FILE [OPTIONS]

Arguments:
  INPUT_FILE    Path to resume YAML or variant file (required)

Options:
  --job, -j PATH_OR_URL_OR_STDIN  Job description file, URL (best-effort), or `-` for stdin (required)
  --provider PROVIDER        AI provider (default: from config)
  --render                   Also render cover letter to PDF (P2 stretch goal — requires cover letter Typst template)
  --output, -o PATH          Output path for cover letter Markdown (default: ./{name}_cover.md)
  -h, --help                 Show help
```

**Examples:**

```bash
# Generate cover letter
anvil cover Jane_Developer_CV.yaml --job https://acme.com/careers/sre

# Generate and render to PDF
anvil cover Jane_Developer_CV.yaml --job https://acme.com/careers/sre --render
```

**LLM failure behavior:** Same as `anvil tailor` (see table above).

---

## `anvil watch`

Monitor GitHub for new activity and suggest resume updates.

**Classification: Extended** — Requires GitHub token.

```
anvil watch [OPTIONS]

Options:
  --github, -g USERNAME      GitHub username (required, or set in config)
  --interval MINUTES         Check interval in minutes (default: 60, minimum: 10)
  --output, -o PATH          Digest output file (default: terminal only)
  --once                     Check once and exit (no polling)
  -h, --help                 Show help
```

**Examples:**

```bash
# Start monitoring
anvil watch --github janedeveloper

# Check once
anvil watch --github janedeveloper --once

# Custom interval with file output
anvil watch --github janedeveloper --interval 120 --output digest.md
```

---

## `anvil deploy`

Deploy resume as a web page.

**Classification: Extended** — Requires Vercel token.

```
anvil deploy INPUT_FILE [OPTIONS]

Arguments:
  INPUT_FILE    Path to resume YAML file (required)

Options:
  --platform PLATFORM        Deployment platform: vercel (default: vercel)
  --project NAME             Vercel project name
  --domain DOMAIN            Custom domain
  --production               Deploy to production (default: preview)
  -h, --help                 Show help
```

**Examples:**

```bash
# Deploy to Vercel preview
anvil deploy Jane_Developer_CV.yaml

# Deploy to production with custom domain
anvil deploy Jane_Developer_CV.yaml --production --domain resume.janedeveloper.com
```

**Error behavior:**

| Condition | Behavior |
|-----------|----------|
| No Vercel token | Exit 4: "Vercel token not found. Set the {VERCEL_TOKEN} environment variable. See https://docs.anvilcv.com/deploy for setup." |
| Vercel API error | Exit 3: "Deployment failed: {error_message}" |

---

## `anvil export`

Export resume in various formats, including rendercv-compatible YAML.

```
anvil export INPUT_FILE [OPTIONS]

Arguments:
  INPUT_FILE    Path to Anvil YAML file (required)

Options:
  --rendercv                 Strip anvil section to produce rendercv-compatible YAML
  --output, -o PATH          Output path
  -h, --help                 Show help
```

**Examples:**

```bash
# Export rendercv-compatible YAML
anvil export Jane_Developer_CV.yaml --rendercv -o Jane_Developer_rendercv.yaml
```
