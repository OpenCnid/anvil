<div align="center">

# ⚒️ Anvil

**Your resume is code. Treat it that way.**

A developer-native, AI-powered resume engine built on [rendercv](https://github.com/rendercv/rendercv).

YAML in → PDF, HTML, ATS-optimized output out.
Score it. Tailor it. Ship it.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests: 929](https://img.shields.io/badge/tests-929%20passing-brightgreen)]()
[![Coverage: 90%](https://img.shields.io/badge/coverage-90%25-brightgreen)]()

</div>

---

## Why Anvil?

You version-control your code, diff your configs, and review PRs for every text artifact you produce — except your resume. That lives in Google Docs, gets copy-pasted between jobs, and gets silently rejected by ATS parsers that can't read your fancy two-column layout.

**Anvil fixes this.** Your resume is a YAML file. You `git diff` it. You branch it per job. You score it against ATS heuristics before submitting. You let AI tailor it to a job description in seconds. You pull real metrics from GitHub instead of guessing.

### What you get

| Problem | Anvil's answer |
|---------|---------------|
| ATS rejects pretty resumes | **Score before you submit** — heuristic checker flags parsing issues |
| Tailoring takes 30-60 min per app | **AI tailoring in seconds** — rewrites bullets to match job language |
| GitHub work doesn't reach your resume | **Auto-import projects** — stars, languages, CI, test coverage |
| No version control for resumes | **It's YAML + git** — branch, diff, merge, track variants |
| Existing tools are visual-first | **Terminal-first** — `anvil render`, `anvil score`, `anvil tailor` |

## Install

```bash
pip install "anvilcv[full]"
```

> Requires Python 3.12+. The `[full]` extra includes PDF rendering (Typst). For a lighter install without PDF: `pip install anvilcv`.

## Quick Start

```bash
# 1. Create a resume from template
anvil new "Jane Developer"

# 2. Edit the YAML with your info
#    (it's just a text file — use any editor)

# 3. Render everything
anvil render Jane_Developer_CV.yaml
```

Output: `PDF` · `PNG` · `HTML` · `ATS HTML` · `Markdown` · `Typst source`

## Commands

### Score your resume (no AI needed)

```bash
# Basic ATS compatibility check
anvil score resume.yaml

# Score against a specific job posting
anvil score resume.yaml --job posting.txt

# Score from a URL
anvil score resume.yaml --job https://acme.com/careers/sre

# Output as YAML for programmatic use
anvil score resume.yaml --format yaml -o report.yaml
```

The scorer checks **16 rules** across parsability, structure, and keyword matching — each tagged as `[evidence-based]` or `[opinionated heuristic]` so you know the confidence level.

```
╭────────────────────────────────────────╮
│        ATS Compatibility Report        │
│             Score: 80/100              │
╰────────────────────────────────────────╯

Parsability: 100/100  ██████████████████████
  ✓ Single-column layout  [evidence based]
  ✓ All text machine-readable  [evidence based]
  ...

Keywords: 40/100  █████████░░░░░░░░░░░░░
  Matched: Python, AWS, Kubernetes
  Missing: Go, Docker, Terraform
  ──────
  ⬆ HIGH: Add "Go" to skills section.
  ⬆ HIGH: Add "Docker" to skills section.
```

### Tailor for a job (AI-powered)

```bash
# Generate a tailored variant
anvil tailor resume.yaml --job posting.txt

# Tailor + render + score in one shot
anvil tailor resume.yaml --job posting.txt --render --score

# Preview changes without writing files
anvil tailor resume.yaml --job posting.txt --dry-run
```

Your original YAML is **never modified**. Tailored variants go to `variants/` with full provenance metadata — which job, which AI provider, what changed.

### Import from GitHub

```bash
# Scan your repos and generate project entries
anvil scan --github janedeveloper

# Merge into your existing resume
anvil scan --github janedeveloper --merge resume.yaml
```

Pulls real metrics: stars, languages, commit counts, CI status, test detection, license. Uses conditional requests (ETag) and aggressive caching to minimize API calls.

### Interview prep & cover letters

```bash
# Generate talking points matched to a job
anvil prep resume.yaml --job posting.txt

# Generate a cover letter that references your actual projects
anvil cover resume.yaml --job posting.txt
```

### More commands

```bash
anvil render resume.yaml --variant ./variants/    # Batch-render all variants
anvil export resume.yaml --rendercv               # Strip anvil section for rendercv compat
anvil new "Name" --theme devforge                  # Use the developer-focused theme
```

## AI Providers

AI features (tailor, prep, cover) support multiple providers:

| Provider | Setup | Notes |
|----------|-------|-------|
| **Anthropic Claude** | `export ANTHROPIC_API_KEY=sk-...` | Recommended. 200K context. |
| **OpenAI GPT-4o** | `export OPENAI_API_KEY=sk-...` | Native JSON mode. |
| **Ollama** | Install Ollama, pull a model | Local, free, no API key. Best-effort quality. |

Or configure defaults in your YAML:

```yaml
anvil:
  providers:
    default: anthropic
    anthropic:
      model: claude-sonnet-4-20250514
      api_key_env: ANTHROPIC_API_KEY
```

## Core features work offline

Anvil splits cleanly between **core** (no keys needed) and **extended** (needs API keys):

| Core (offline) | Extended (needs keys) |
|----------------|----------------------|
| `anvil render` | `anvil tailor` |
| `anvil score` | `anvil prep` |
| `anvil new` | `anvil cover` |
| `anvil export` | `anvil scan`* |

*`scan` needs a GitHub token for useful rate limits but works without one (60 req/hr).

## rendercv Compatibility

**100% backward compatible.** Every valid rendercv YAML file renders identically through Anvil. The extended `anvil` section is optional — omit it entirely and Anvil behaves exactly like rendercv.

```bash
# Works with any existing rendercv file
anvil render my_existing_rendercv_resume.yaml

# Export back to pure rendercv format
anvil export my_anvil_resume.yaml --rendercv
```

## Built on rendercv

Anvil is a hard fork of [rendercv](https://github.com/rendercv/rendercv) v2.7 by [Sina Atalay](https://github.com/sinaatalay). Everything great about rendercv is still here:

- YAML input → beautiful PDF output via Typst
- 5 built-in themes + custom theme support
- JSON Schema for editor autocompletion
- Strict validation with clear error messages
- Locale/i18n support for dates and section headers
- Watch mode for live reload during editing

Anvil adds the intelligence layer on top.

## License

MIT — same as rendercv.
