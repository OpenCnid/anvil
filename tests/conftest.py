"""Shared test fixtures for the AnvilCV test suite.

Why:
    Centralizes common test setup (temp directories, sample YAML files, mock
    providers) so individual test files stay focused on assertions. The
    compatibility corpus fixture provides real rendercv YAML for integration
    tests that verify byte-identical rendering.
"""

import pathlib

import pytest


@pytest.fixture
def sample_rendercv_yaml(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal valid rendercv YAML file (no anvil section)."""
    yaml_content = """\
cv:
  name: John Doe
  location: San Francisco, CA
  email: john@example.com
  sections:
    experience:
      - company: Acme Corp
        position: Software Engineer
        start_date: 2020-01
        end_date: present
        highlights:
          - Built scalable microservices serving 1M+ requests/day
          - Led migration from monolith to event-driven architecture
    education:
      - institution: MIT
        area: Computer Science
        degree: BS
        start_date: 2016-09
        end_date: 2020-05
    skills:
      - label: Languages
        details: Python, TypeScript, Go, Rust
      - label: Frameworks
        details: FastAPI, React, Django
"""
    yaml_file = tmp_path / "John_Doe_CV.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file


@pytest.fixture
def sample_anvil_yaml(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create an Anvil-extended YAML file (with anvil section)."""
    yaml_content = """\
cv:
  name: Jane Developer
  location: New York, NY
  email: jane@example.com
  sections:
    experience:
      - company: TechCo
        position: Senior Engineer
        start_date: 2021-06
        end_date: present
        highlights:
          - Designed real-time data pipeline processing 500K events/sec
    education:
      - institution: Stanford
        area: Computer Science
        degree: MS
        start_date: 2019-09
        end_date: 2021-06
    skills:
      - label: Languages
        details: Python, Go, Rust
anvil:
  providers:
    default: anthropic
    anthropic:
      model: claude-sonnet-4-20250514
"""
    yaml_file = tmp_path / "Jane_Developer_CV.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file
