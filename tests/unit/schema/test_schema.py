"""Tests for the Anvil extended YAML schema.

Why:
    The schema is the data contract between user YAML and all Anvil features.
    We verify:
    - rendercv YAML without `anvil` section validates identically to rendercv
    - `anvil` section validates correctly with all sub-models
    - Unknown fields are rejected (strict validation)
    - Clear error messages on invalid input
    - Model builder wraps vendored builder correctly
"""

import pathlib
from datetime import datetime

import pydantic
import pytest

from anvilcv.schema.anvil_config import (
    AnthropicProviderConfig,
    AnvilConfig,
    DeployConfig,
    GitHubConfig,
    OllamaProviderConfig,
    OpenAIProviderConfig,
    ProvidersConfig,
    VariantsConfig,
)
from anvilcv.schema.anvil_model import AnvilModel
from anvilcv.schema.github_profile import (
    GitHubProfile,
    GitHubRepo,
    GitHubSummary,
    RepoMetrics,
)
from anvilcv.schema.job_description import JobDescription, JobRequirements
from anvilcv.schema.model_builder import (
    build_anvil_dictionary_and_model,
    build_anvil_model_from_commented_map,
)
from anvilcv.schema.score_report import (
    Check,
    KeywordMatchSection,
    Recommendation,
    ScoreReport,
    SectionScore,
)
from anvilcv.schema.variant import VariantChange, VariantMetadata

# --- AnvilModel: rendercv compatibility ---


class TestRendercvCompatibility:
    def test_rendercv_yaml_without_anvil_validates(self, sample_rendercv_yaml: pathlib.Path):
        """rendercv YAML without anvil section should validate as AnvilModel."""
        yaml_content = sample_rendercv_yaml.read_text()
        _, model = build_anvil_dictionary_and_model(
            yaml_content, input_file_path=sample_rendercv_yaml
        )
        assert isinstance(model, AnvilModel)
        assert model.anvil is None
        assert model.cv.name == "John Doe"

    def test_anvil_yaml_with_anvil_section_validates(self, sample_anvil_yaml: pathlib.Path):
        """Anvil YAML with anvil section should validate."""
        yaml_content = sample_anvil_yaml.read_text()
        _, model = build_anvil_dictionary_and_model(yaml_content, input_file_path=sample_anvil_yaml)
        assert isinstance(model, AnvilModel)
        assert model.anvil is not None
        assert model.anvil.providers.default == "anthropic"
        assert model.cv.name == "Jane Developer"

    def test_empty_anvil_section_uses_defaults(self):
        """An empty `anvil:` section should use all defaults."""
        yaml = "cv:\n  name: Test\ndesign:\n  theme: classic\nanvil: {}\n"
        _, model = build_anvil_dictionary_and_model(yaml)
        assert model.anvil is not None
        assert model.anvil.providers.default == "anthropic"
        assert model.anvil.github is None
        assert model.anvil.deploy is None

    def test_unknown_top_level_key_rejected(self):
        """Unknown top-level keys should be rejected."""
        yaml = "cv:\n  name: Test\nunknown_key: bad\n"
        with pytest.raises(Exception):
            build_anvil_dictionary_and_model(yaml)

    def test_unknown_anvil_field_rejected(self):
        """Unknown fields inside anvil section should be rejected."""
        yaml = "cv:\n  name: Test\nanvil:\n  unknown_field: bad\n"
        with pytest.raises(Exception):
            build_anvil_dictionary_and_model(yaml)


# --- AnvilConfig sub-models ---


class TestAnvilConfig:
    def test_providers_defaults(self):
        config = AnvilConfig()
        assert config.providers.default == "anthropic"
        assert config.providers.anthropic.model == "claude-sonnet-4-20250514"
        assert config.providers.openai.model == "gpt-4o"
        assert config.providers.ollama.model == "llama3.1:8b"

    def test_providers_custom(self):
        config = AnvilConfig(
            providers=ProvidersConfig(
                default="openai",
                openai=OpenAIProviderConfig(model="gpt-4-turbo"),
            )
        )
        assert config.providers.default == "openai"
        assert config.providers.openai.model == "gpt-4-turbo"

    def test_invalid_default_provider_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            ProvidersConfig(default="nonexistent")

    def test_github_config(self):
        config = GitHubConfig(
            username="janedeveloper",
            exclude_repos=["dotfiles"],
            min_commits=10,
        )
        assert config.username == "janedeveloper"
        assert config.include_forks is False
        assert config.min_stars == 0
        assert config.min_commits == 10

    def test_github_negative_min_stars_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            GitHubConfig(username="test", min_stars=-1)

    def test_variants_defaults(self):
        config = VariantsConfig()
        assert config.output_dir == "./variants"
        assert "{name}" in config.naming

    def test_deploy_config(self):
        config = DeployConfig(
            project_name="my-resume",
            domain="resume.example.com",
        )
        assert config.platform == "vercel"
        assert config.project_name == "my-resume"

    def test_unknown_provider_field_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            AnthropicProviderConfig(model="test", unknown_field="bad")

    def test_ollama_custom_base_url(self):
        config = OllamaProviderConfig(base_url="http://gpu-server:11434")
        assert config.base_url == "http://gpu-server:11434"


# --- JobDescription ---


class TestJobDescription:
    def test_minimal_job(self):
        job = JobDescription(title="SRE", company="Acme")
        assert job.title == "SRE"
        assert job.source == "file"
        assert job.requirements.required_skills == []
        assert job.raw_text == ""

    def test_full_job(self):
        job = JobDescription(
            title="Senior SRE",
            company="Acme Corp",
            url="https://acme.com/jobs/sre",
            source="url",
            requirements=JobRequirements(
                required_skills=["Kubernetes", "Python"],
                preferred_skills=["Terraform"],
                experience_years=5,
                education="BS Computer Science",
            ),
            raw_text="We are looking for...",
        )
        assert len(job.requirements.required_skills) == 2
        assert job.requirements.experience_years == 5

    def test_negative_experience_years_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            JobRequirements(experience_years=-1)

    def test_invalid_source_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            JobDescription(title="Test", company="Test", source="invalid")


# --- VariantMetadata ---


class TestVariantMetadata:
    def test_variant_metadata(self):
        meta = VariantMetadata(
            source="./cv.yaml",
            job=".anvil/jobs/acme.yaml",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            changes=[
                VariantChange(
                    section="experience.0.highlights",
                    action="rewritten",
                    detail="Emphasized Kubernetes experience",
                ),
            ],
        )
        assert meta.provider == "anthropic"
        assert len(meta.changes) == 1
        assert meta.changes[0].action == "rewritten"
        assert isinstance(meta.created_at, datetime)


# --- GitHubProfile ---


class TestGitHubProfile:
    def test_github_repo(self):
        repo = GitHubRepo(
            name="k8s-autoscaler",
            url="https://github.com/user/k8s-autoscaler",
            stars=234,
            primary_language="Go",
            languages={"Go": 85.2, "Shell": 14.8},
            topics=["kubernetes"],
            metrics=RepoMetrics(
                total_commits=312,
                has_tests=True,
                has_ci=True,
                license="MIT",
            ),
        )
        assert repo.stars == 234
        assert repo.metrics.has_ci is True

    def test_github_profile(self):
        profile = GitHubProfile(
            username="janedeveloper",
            repos=[
                GitHubRepo(
                    name="repo1",
                    url="https://github.com/user/repo1",
                ),
            ],
            summary=GitHubSummary(
                total_repos=1,
                total_stars=10,
                primary_languages=["Python"],
            ),
        )
        assert len(profile.repos) == 1
        assert profile.summary.total_repos == 1


# --- ScoreReport ---


class TestScoreReport:
    def test_score_report_without_job(self):
        report = ScoreReport(
            file="./cv.pdf",
            overall_score=78,
            parsability=SectionScore(
                score=90,
                checks=[
                    Check(
                        name="Single-column layout",
                        status="pass",
                        confidence="evidence_based",
                    ),
                ],
            ),
            structure=SectionScore(score=85),
        )
        assert report.overall_score == 78
        assert report.keyword_match is None
        assert report.parsability.checks[0].status == "pass"

    def test_score_report_with_keywords(self):
        report = ScoreReport(
            file="./cv.pdf",
            overall_score=72,
            parsability=SectionScore(score=90),
            structure=SectionScore(score=85),
            keyword_match=KeywordMatchSection(
                score=65,
                job_keywords=["Python", "Kubernetes"],
                matched=["Python"],
                missing=["Kubernetes"],
            ),
            recommendations=[
                Recommendation(
                    priority="high",
                    message="Add Kubernetes to skills",
                ),
            ],
        )
        assert report.keyword_match is not None
        assert len(report.keyword_match.missing) == 1
        assert report.recommendations[0].priority == "high"

    def test_score_out_of_range_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            ScoreReport(file="test.pdf", overall_score=101)

    def test_invalid_check_status_rejected(self):
        with pytest.raises(pydantic.ValidationError):
            Check(name="test", status="invalid")


# --- Model Builder ---


class TestModelBuilder:
    def test_build_from_commented_map(self):
        data = {
            "cv": {"name": "Test User"},
            "anvil": {
                "providers": {"default": "openai"},
            },
        }
        model = build_anvil_model_from_commented_map(data)
        assert isinstance(model, AnvilModel)
        assert model.anvil.providers.default == "openai"

    def test_build_from_yaml_string(self):
        yaml = "cv:\n  name: Test User\nanvil:\n  providers:\n    default: ollama\n"
        _, model = build_anvil_dictionary_and_model(yaml)
        assert model.anvil.providers.default == "ollama"

    def test_build_preserves_rendercv_fields(self, sample_rendercv_yaml: pathlib.Path):
        yaml_content = sample_rendercv_yaml.read_text()
        _, model = build_anvil_dictionary_and_model(
            yaml_content, input_file_path=sample_rendercv_yaml
        )
        assert model.cv.name == "John Doe"
        assert model.cv.location == "San Francisco, CA"

    def test_build_with_variant_metadata(self):
        yaml = (
            "cv:\n  name: Test\n"
            "variant:\n"
            "  source: ./cv.yaml\n"
            "  provider: anthropic\n"
            "  model: claude-sonnet-4-20250514\n"
        )
        _, model = build_anvil_dictionary_and_model(yaml)
        assert model.variant is not None
        assert model.variant.provider == "anthropic"
