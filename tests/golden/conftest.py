"""Fixtures and markers for Tier 2 golden-set regression tests.

Why:
    Golden-set tests run against live AI APIs and are expensive. They should
    only execute during nightly CI runs or on explicit request (--run-golden).
    This conftest registers the 'golden' marker and provides fixtures for
    loading test cases, resolving providers, and tracking baseline scores.
"""

from __future__ import annotations

import os
import pathlib

import pytest
from ruamel.yaml import YAML

GOLDEN_DIR = pathlib.Path(__file__).parent

yaml = YAML()
yaml.preserve_quotes = True


def pytest_configure(config: pytest.Config) -> None:
    """Register the 'golden' marker for Tier 2 golden-set tests."""
    config.addinivalue_line(
        "markers",
        "golden: Tier 2 golden-set regression test (requires live AI APIs, run with --run-golden)",
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --run-golden CLI option to pytest."""
    parser.addoption(
        "--run-golden",
        action="store_true",
        default=False,
        help="Run Tier 2 golden-set regression tests (requires live AI API keys)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip golden-set tests unless --run-golden is specified."""
    if config.getoption("--run-golden"):
        return

    skip_golden = pytest.mark.skip(
        reason="Golden-set tests require --run-golden flag and live API keys"
    )
    for item in items:
        if "golden" in item.keywords:
            item.add_marker(skip_golden)


@pytest.fixture
def golden_dir() -> pathlib.Path:
    """Path to the golden test directory."""
    return GOLDEN_DIR


def load_case_data(feature: str, case_name: str) -> tuple[dict, dict, list[dict]]:
    """Load input resume, job description, and rubric for a golden-set case.

    Returns:
        Tuple of (resume_data, job_data, rubric_criteria).
    """
    case_dir = GOLDEN_DIR / feature / case_name

    with open(case_dir / "input_resume.yaml") as f:
        resume_data = yaml.load(f)

    with open(case_dir / "input_job.yaml") as f:
        job_data = yaml.load(f)

    with open(case_dir / "expected_rubric.yaml") as f:
        rubric_data = yaml.load(f)

    return resume_data, job_data, rubric_data.get("rubric", [])


def provider_available(provider_name: str) -> bool:
    """Check if a provider's API key or service is available."""
    if provider_name == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    elif provider_name == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    elif provider_name == "ollama":
        try:
            import httpx

            resp = httpx.get("http://localhost:11434/api/version", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False
    return False


def get_provider(provider_name: str):
    """Instantiate an AI provider by name.

    Returns None if provider is not available.
    """
    if not provider_available(provider_name):
        return None

    if provider_name == "anthropic":
        from anvilcv.ai.anthropic import AnthropicProvider

        return AnthropicProvider()
    elif provider_name == "openai":
        from anvilcv.ai.openai import OpenAIProvider

        return OpenAIProvider()
    elif provider_name == "ollama":
        from anvilcv.ai.ollama import OllamaProvider

        return OllamaProvider()
    return None
