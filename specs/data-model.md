# Data Model

## Schema Design Strategy

Anvil extends rendercv's YAML schema by adding a top-level `anvil` section alongside the existing `cv`, `design`, `locale`, and `settings` sections. rendercv's core models are NOT modified — Anvil fields live in a separate namespace.

## Schema Compatibility Contract

### Guarantees

1. **Any valid rendercv v2.7 YAML file is valid Anvil YAML.** Anvil reads it, validates it, and renders it identically to rendercv v2.7.
2. **The `anvil` section is optional.** Omitting it entirely produces behavior identical to rendercv.
3. **rendercv ignores the `anvil` section.** rendercv's `BaseModelWithoutExtraKeys` rejects unknown top-level keys, so rendercv CANNOT read Anvil YAML that includes the `anvil` section. This is expected and documented. Users who want rendercv compatibility should maintain a copy without the `anvil` section (or use `anvil export --rendercv` to strip it).

### Unknown Field Behavior

| Context | Behavior |
|---------|----------|
| Unknown field inside `cv`, `design`, `locale`, `settings` | **Error** (matches rendercv behavior — `BaseModelWithoutExtraKeys` forbids extras) |
| Unknown field inside `anvil` section | **Error** (Anvil's config model also forbids extras for safety) |
| Top-level key other than `cv`, `design`, `locale`, `settings`, `anvil` | **Error** (matches rendercv strictness + Anvil's own strictness) |
| rendercv YAML with no `anvil` section | **Valid** (renders identically to rendercv) |

## Extended YAML Schema

### Root Model: `AnvilModel`

```yaml
# Standard rendercv fields (unchanged):
cv:
  name: "Jane Developer"
  # ... all rendercv cv fields ...

design:
  theme: classic  # or any rendercv theme, or new Anvil themes
  # ... all rendercv design fields ...

locale:
  # ... all rendercv locale fields ...

settings:
  # ... all rendercv settings fields ...

# NEW — Anvil-specific configuration:
anvil:
  # Provider configuration for AI features
  providers:
    default: anthropic  # Which provider to use when not specified per-command
    anthropic:
      model: claude-sonnet-4-20250514
      api_key_env: ANTHROPIC_API_KEY  # Environment variable name (NOT the key itself)
    openai:
      model: gpt-4o
      api_key_env: OPENAI_API_KEY
    ollama:
      model: llama3.1:8b
      base_url: http://localhost:11434

  # GitHub integration
  github:
    username: janedeveloper
    token_env: GITHUB_TOKEN  # Environment variable name
    include_repos: []  # Empty = all public repos. List specific repo names to filter.
    exclude_repos: ["dotfiles", "old-project"]
    include_forks: false
    min_stars: 0
    min_commits: 5  # Only include repos where user has ≥ this many commits

  # Variant tracking
  variants:
    output_dir: "./variants"  # Where tailored variants are written
    naming: "{name}_{company}_{date}"  # Naming template for variant files

  # Deployment
  deploy:
    platform: vercel
    token_env: VERCEL_TOKEN
    project_name: jane-resume
    domain: resume.janedeveloper.com  # Optional custom domain
```

### Job Description Model

Job descriptions are stored as separate YAML files or inline in the `anvil tailor` command output:

```yaml
# .anvil/jobs/acme-sre-2024-03.yaml
job:
  title: "Senior Site Reliability Engineer"
  company: "Acme Corp"
  url: "https://acme.com/careers/sre-senior"
  fetched_at: "2026-03-10T14:30:00Z"
  source: url  # "url" (fetched via best-effort heuristic parsing), "file" (from local file), or "stdin" (piped via --job -)

  # Parsed from job description (by heuristic parser or AI-enhanced parser):
  requirements:
    required_skills: ["Kubernetes", "Terraform", "Python", "Go"]
    preferred_skills: ["Prometheus", "Grafana", "AWS"]
    experience_years: 5
    education: "BS Computer Science or equivalent"

  # Raw text (preserved for AI consumption):
  raw_text: |
    We are looking for a Senior SRE to join our platform team...
    Requirements:
    - 5+ years experience with distributed systems
    ...
```

### Variant Model

Each tailored variant is a full Anvil YAML file with provenance metadata:

```yaml
# variants/Jane_Developer_Acme_SRE_2026-03-10.yaml

cv:
  name: "Jane Developer"
  # ... full CV content with tailored bullets and reordered sections ...

design:
  theme: devforge

anvil:
  variant:
    source: "./Jane_Developer_CV.yaml"  # Path to source YAML
    job: ".anvil/jobs/acme-sre-2024-03.yaml"  # Path to job description
    created_at: "2026-03-10T15:00:00Z"
    provider: anthropic  # Which AI provider generated this variant
    model: claude-sonnet-4-20250514
    changes:
      - section: "projects"
        action: "reordered"
        detail: "Moved k8s-autoscaler to position 1 (was 3)"
      - section: "experience.0.highlights"
        action: "rewritten"
        detail: "Emphasized Kubernetes and Terraform experience"
      - section: "skills"
        action: "reordered"
        detail: "Moved Infrastructure & DevOps to position 1"
```

### GitHub Profile Model

GitHub scan results are stored as YAML for later use in tailoring:

```yaml
# .anvil/github/janedeveloper.yaml
github:
  username: janedeveloper
  scanned_at: "2026-03-10T12:00:00Z"
  rate_limit_remaining: 4832

  repos:
    - name: k8s-autoscaler
      description: "Kubernetes HPA custom metrics autoscaler"
      url: "https://github.com/janedeveloper/k8s-autoscaler"
      stars: 234
      forks: 45
      primary_language: Go
      languages: { Go: 85.2, Shell: 10.1, Dockerfile: 4.7 }
      topics: ["kubernetes", "autoscaling", "devops"]
      created_at: "2024-01-15"
      last_push: "2026-02-28"
      default_branch: main
      metrics:
        total_commits: 312
        user_commits: 289
        open_issues: 3
        contributors: 8
        has_tests: true
        has_ci: true
        license: MIT

    - name: ml-pipeline-framework
      # ... similar structure ...

  # Aggregated stats
  summary:
    total_repos: 23
    total_stars: 567
    primary_languages: ["Go", "Python", "TypeScript"]
    total_commits: 2341
    active_repos_last_90_days: 8
```

### ATS Score Report Model

```yaml
# Output of `anvil score`
score_report:
  file: "./Jane_Developer_CV.pdf"
  scored_at: "2026-03-10T15:30:00Z"
  overall_score: 78  # 0-100

  # Optional: scored against a specific job description
  job: ".anvil/jobs/acme-sre-2024-03.yaml"

  sections:
    parsability:
      score: 90
      checks:
        - name: "Single-column layout"
          status: pass
          confidence: evidence_based
          source: "Jobscan 2023 ATS study"
        - name: "Standard section headers"
          status: pass
          confidence: evidence_based
        - name: "No embedded images"
          status: pass
          confidence: evidence_based
        - name: "Machine-readable dates"
          status: warn
          detail: "Date format 'Jan 2024' detected; 'January 2024' is safer"
          confidence: opinionated_heuristic

    keyword_match:
      score: 65
      job_keywords: ["Kubernetes", "Terraform", "Python", "Go", "SRE"]
      matched: ["Python", "Go", "Kubernetes"]
      missing: ["Terraform", "SRE"]
      partial: []

    structure:
      score: 85
      checks:
        - name: "Contact info present"
          status: pass
        - name: "Experience section detected"
          status: pass
        - name: "Education section detected"
          status: pass
        - name: "Skills section detected"
          status: pass
        - name: "Resume length"
          status: pass
          detail: "1 page (recommended for < 10 years experience)"
          confidence: opinionated_heuristic

  recommendations:
    - priority: high
      message: "Add 'Terraform' to skills — required by job description"
    - priority: medium
      message: "Consider adding 'SRE' or 'Site Reliability' to headline or summary"
    - priority: low
      message: "Use full month names in dates for maximum ATS compatibility"
```

## Data Flow Between Commands

| Command | Reads | Writes |
|---------|-------|--------|
| `anvil render` | User YAML | PDF, Typst, Markdown, HTML, PNG, ATS HTML |
| `anvil score` | Rendered PDF/HTML + optional job YAML | Score report (YAML + terminal output) |
| `anvil scan` | GitHub API | GitHub profile YAML (`.anvil/github/`) |
| `anvil tailor` | User YAML + job description (URL or file) | Variant YAML + job YAML (`.anvil/jobs/`) |
| `anvil prep` | User YAML (or variant) + job YAML | Prep notes (Markdown) |
| `anvil cover` | User YAML (or variant) + job YAML | Cover letter (Markdown). PDF via `--render` is P2 stretch goal. |
| `anvil watch` | GitHub API (polling) | Digest notifications (terminal or file) |
| `anvil deploy` | User YAML (or variant) | Deployed URL |

## File System Layout

```
my-resume/
├── Jane_Developer_CV.yaml          # Source YAML (user-maintained)
├── .anvil/                         # Anvil working directory
│   ├── config.yaml                 # Local config overrides (gitignored)
│   ├── github/                     # GitHub scan cache
│   │   └── janedeveloper.yaml
│   ├── jobs/                       # Parsed job descriptions
│   │   ├── acme-sre-2024-03.yaml
│   │   └── startup-backend-2024-03.yaml
│   └── debug/                      # Debug output from failed AI requests
│       └── tailor_2026-03-10_150000.txt
├── variants/                       # Tailored variants (git-trackable)
│   ├── Jane_Developer_Acme_SRE_2026-03-10.yaml
│   └── Jane_Developer_Startup_Backend_2026-03-10.yaml
└── output/                         # Rendered output (gitignored)
    ├── Jane_Developer_CV.pdf
    ├── Jane_Developer_CV.typ
    ├── Jane_Developer_CV.md
    ├── Jane_Developer_CV.html
    ├── Jane_Developer_CV_ats.html  # ATS-optimized HTML
    └── Jane_Developer_CV_1.png
```
