# Anvil

Developer-native, AI-powered resume engine. A fork of [rendercv](https://github.com/rendercv/rendercv) v2.7 with ATS optimization, AI tailoring, and GitHub integration — all driven from YAML.

## Install

```bash
pip install "anvilcv[full]"
```

Requires Python 3.12+. The `[full]` extra includes PDF rendering dependencies. For a lighter install without PDF support: `pip install anvilcv`.

## Quick Start

```bash
# Create a new resume from a template
anvil new "Your Name"

# Render to PDF, HTML, Markdown, and ATS-optimized HTML
anvil render Your_Name_CV.yaml

# Check ATS compatibility (heuristic, no AI needed)
anvil score Your_Name_CV.yaml

# Score against a specific job description
anvil score Your_Name_CV.yaml --job posting.txt

# Tailor your resume for a job (requires AI provider)
anvil tailor Your_Name_CV.yaml --job posting.txt --provider anthropic

# Generate interview prep notes
anvil prep Your_Name_CV.yaml --job posting.txt

# Generate a cover letter
anvil cover Your_Name_CV.yaml --job posting.txt

# Import GitHub projects into your resume
anvil scan --github your-username --merge Your_Name_CV.yaml
```

## Features

**100% backward compatible** — every valid rendercv YAML file renders identically through Anvil.

- **ATS score checker** — heuristic scoring (parsability, structure, keyword match) with actionable recommendations. No AI required.
- **AI job tailoring** — rewrite bullets to match a job description, producing a variant YAML with full provenance metadata. Supports Anthropic Claude, OpenAI GPT, and Ollama (local).
- **ATS-optimized HTML** — semantic `<section>`/`<article>` markup generated alongside standard outputs for maximum ATS parseability.
- **devforge theme** — single-column, ATS-safe theme with skill chips, GitHub-style project metadata lines, and responsive HTML.
- **GitHub scanner** — fetch your repos via the GitHub API, extract languages/stars/CI/test info, and generate resume entries automatically. Conditional requests and aggressive caching.
- **Interview prep** — AI-generated talking points matched to job requirements and your actual projects.
- **Cover letter generation** — non-generic cover letters that reference your real experience and projects.
- **Multi-variant rendering** — maintain base + tailored variants in `variants/`, render all at once.
- **JSON Schema** — full schema for VS Code YAML autocompletion of the extended `anvil` config section.
- **rendercv export** — strip the `anvil` section to produce a pure rendercv YAML file.

## AI Providers

Anvil's AI features (tailor, prep, cover) work with multiple providers. Set your API key and go:

```bash
export ANTHROPIC_API_KEY=sk-...    # Claude (recommended)
export OPENAI_API_KEY=sk-...       # GPT-4o
# Or use Ollama locally — no API key needed
```

Configure defaults in your YAML under the `anvil.providers` section.

## License

MIT
