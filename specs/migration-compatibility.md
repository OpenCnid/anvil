# Migration & Compatibility

## Migration Path for rendercv Users

### What Just Works (Zero Changes)

Any valid rendercv v2.7 YAML file works with Anvil immediately:

```bash
# This works — Anvil renders it identically to rendercv
anvil render My_CV.yaml
```

No migration step. No conversion tool. No schema changes. Anvil reads the file, validates it using the same Pydantic models as rendercv, and produces identical output.

### What's New (Optional Opt-In)

Users who want Anvil-specific features add the `anvil` section:

```yaml
# Existing rendercv fields (unchanged)
cv:
  name: "Jane Developer"
  ...
design:
  theme: classic
  ...

# NEW — opt-in to Anvil features
anvil:
  providers:
    default: anthropic
    ...
```

### What Breaks (Nothing — by Design)

Anvil does not deprecate, remove, or change any rendercv feature. All 5 built-in themes (classic, moderncv, sb2nov, engineeringresumes, engineeringclassic) are preserved. All CLI flags from `rendercv render` work with `anvil render`. The only breaking change is the binary name (`anvil` instead of `rendercv`).

Users who want both installed simultaneously: Anvil's package name is `anvilcv`, so `pip install anvilcv` does not conflict with `pip install rendercv`. Both binaries can coexist.

## Compatibility Test Corpus

### Requirement

Anvil's CI MUST include a compatibility test corpus of real rendercv YAML files that must render through Anvil without errors. This is the enforcement mechanism for forward compatibility.

### Corpus Contents

The corpus includes:

1. **rendercv example files** — All YAML files from `rendercv/examples/` in the v2.7 release (one per theme)
2. **Edge case files** — Manually crafted YAML files testing:
   - Empty sections
   - Single-entry sections
   - All entry types (bullet, education, experience, normal, numbered, one_line, publication, text)
   - Maximum field lengths
   - Unicode content (names, locations with accents/non-Latin characters)
   - Multiple email/phone/website fields (list syntax)
   - Custom connections
   - Photo field (URL and relative path variants)
   - All 5 built-in themes
   - Locale overrides (non-English date labels)
   - Settings overrides (output directory, render flags)
   - Design overrides (overlay files)
3. **Community contributions** — At least 5 real-world rendercv YAML files sourced from public GitHub repos (with permission or from MIT-licensed repos)

**Minimum corpus size:** 20 files.

### "Identical" Definition

For compatibility testing, "identical" means:

| Output | Comparison Method | Tolerance |
|--------|------------------|-----------|
| Typst source (`.typ`) | Byte-identical string comparison | Zero tolerance — exact match |
| Markdown (`.md`) | Byte-identical string comparison | Zero tolerance — exact match |
| HTML (`.html`) | Byte-identical string comparison | Zero tolerance — exact match |
| PDF (`.pdf`) | NOT compared — Typst binary rendering may vary by platform/version | N/A |
| PNG (`.png`) | NOT compared — derived from PDF | N/A |

**Rationale:** Typst source is the authoritative intermediate format. If the Typst source is byte-identical, the PDF will be visually identical (any differences would come from the Typst compiler, not Anvil). Comparing PDFs across platforms introduces false positives from font rendering, metadata timestamps, and compression differences.

### CI Integration

```yaml
# In Anvil's CI pipeline:
- name: Compatibility corpus test
  run: |
    for file in tests/corpus/*.yaml; do
      # Render with Anvil
      anvil render "$file" --output-dir /tmp/anvil_output/
      # Render with rendercv (installed as test dependency)
      rendercv render "$file" --output-dir /tmp/rendercv_output/
      # Compare Typst output
      diff /tmp/anvil_output/*.typ /tmp/rendercv_output/*.typ
      # Compare Markdown output
      diff /tmp/anvil_output/*.md /tmp/rendercv_output/*.md
      # Compare HTML output
      diff /tmp/anvil_output/*.html /tmp/rendercv_output/*.html
    done
```

### Corpus Maintenance

When rendercv releases a new version:

1. Update the example files in the corpus from the new release
2. Run the corpus tests against Anvil
3. If any test fails, this is a **regression** — fix Anvil, don't remove the test
4. Add new edge case files for any new rendercv features

## rendercv Features Anvil Does NOT Carry Forward

None. Anvil carries forward 100% of rendercv v2.7 features. No deprecations in v1.

If a future Anvil version needs to diverge from a rendercv feature (e.g., replacing a theme implementation), this decision will be documented as:
- The rendercv feature being replaced
- The Anvil replacement
- A migration guide
- A deprecation period (minimum 1 minor version)

## Version Detection

Anvil YAML files are identified by the presence of the `anvil` top-level key. There is no explicit version field in v1.

If future Anvil versions need schema versioning:

```yaml
anvil:
  version: 2  # Future — not in v1
  ...
```

For v1, the absence of `anvil.version` implies v1 schema.

## Installing Alongside rendercv

```bash
# Both can be installed simultaneously
pip install rendercv     # Provides `rendercv` binary
pip install anvilcv      # Provides `anvil` binary

# No conflicts — different package names, different binaries
rendercv render my_cv.yaml   # Uses rendercv
anvil render my_cv.yaml      # Uses Anvil (identical output for rendercv YAML)
```

## Migration Checklist for rendercv Users

1. ✅ Install Anvil: `pip install anvilcv`
2. ✅ Run `anvil render your_cv.yaml` — verify identical output
3. ✅ (Optional) Add `anvil:` section for AI features
4. ✅ (Optional) Try `anvil score your_cv.yaml` for ATS analysis
5. ✅ (Optional) Try new themes: change `design.theme` to `devforge` or `terminal`
