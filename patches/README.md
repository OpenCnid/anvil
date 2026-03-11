# Patch Index

Modifications to vendored rendercv v2.7 code are tracked here.

| Patch | File Modified | Purpose | Risk Level |
|-------|--------------|---------|------------|
| P-001 | `vendor/rendercv/__init__.py` | Package identity: version from anvilcv, description updated | **Low** |
| P-002 | `vendor/rendercv/__main__.py` | Redirect `python -m` to Anvil entry point | **Low** |
| P-003 | `vendor/rendercv/cli/entry_point.py` | Redirect CLI entry point to Anvil | **Low** |
| P-004 | `vendor/rendercv/cli/app.py` | Replace Typer app with Anvil's; vendored command auto-discovery preserved | **Medium** |

Risk levels:
- **Low** — Simple additions or renames. Unlikely to conflict with upstream.
- **Medium** — Structural changes. May conflict with upstream refactors.
- **High** — Deep behavioral changes. Will likely conflict with upstream.
