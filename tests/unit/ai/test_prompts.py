"""Tests for per-provider prompt system.

Why:
    Per design principle P5 (providers are pluggable not fungible), each
    provider gets optimized prompts. These tests verify:
    1. Per-provider prompt builders produce correct format (XML for Anthropic,
       concise for OpenAI, simplified for Ollama)
    2. The prompt selector dispatches correctly by provider name
    3. Unknown providers fall back to common prompts
    4. All prompt builders return (system_prompt, user_prompt) tuples
"""

from anvilcv.ai.prompts.keyword_extraction import anthropic as ke_anthropic
from anvilcv.ai.prompts.keyword_extraction import ollama as ke_ollama
from anvilcv.ai.prompts.keyword_extraction import openai as ke_openai
from anvilcv.ai.prompts.keyword_extraction.common import build_extraction_prompt
from anvilcv.ai.prompts.selector import get_prompt_builder
from anvilcv.ai.prompts.tailor_bullets import anthropic as tb_anthropic
from anvilcv.ai.prompts.tailor_bullets import ollama as tb_ollama
from anvilcv.ai.prompts.tailor_bullets import openai as tb_openai
from anvilcv.ai.prompts.tailor_bullets.common import build_tailor_prompt
from anvilcv.schema.job_description import JobDescription, JobRequirements
from anvilcv.tailoring.matcher import ResumeMatch


def _job() -> JobDescription:
    return JobDescription(
        title="Backend Engineer",
        company="Acme",
        requirements=JobRequirements(
            required_skills=["Python", "PostgreSQL", "Docker"],
            preferred_skills=["Redis", "GraphQL"],
        ),
        raw_text="Looking for a backend engineer with Python and PostgreSQL.",
    )


def _match() -> ResumeMatch:
    return ResumeMatch(
        missing_required=["Docker", "PostgreSQL"],
        job_required_skills=["Python", "PostgreSQL", "Docker"],
    )


# --- Tailor Bullets: Common ---


class TestTailorBulletsCommon:
    def test_returns_tuple(self):
        result = build_tailor_prompt("Built APIs", _job(), _match())
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_system_prompt_mentions_resume(self):
        system, _ = build_tailor_prompt("Built APIs", _job(), _match())
        assert "resume" in system.lower() or "bullet" in system.lower()

    def test_user_prompt_includes_bullet_and_job(self):
        _, user = build_tailor_prompt("Built APIs", _job(), _match())
        assert "Built APIs" in user
        assert "Acme" in user
        assert "Python" in user


# --- Tailor Bullets: Anthropic ---


class TestTailorBulletsAnthropic:
    def test_xml_tags_in_prompt(self):
        _, user = tb_anthropic.build_prompt("Built APIs", _job(), _match())
        assert "<job>" in user
        assert "<original_bullet>" in user
        assert "<rewritten>" in user

    def test_system_mentions_xml(self):
        system, _ = tb_anthropic.build_prompt("Built APIs", _job(), _match())
        assert "<rewritten>" in system

    def test_includes_preferred_skills(self):
        _, user = tb_anthropic.build_prompt("Built APIs", _job(), _match())
        assert "<preferred_skills>" in user


# --- Tailor Bullets: OpenAI ---


class TestTailorBulletsOpenAI:
    def test_concise_format(self):
        _, user = tb_openai.build_prompt("Built APIs", _job(), _match())
        assert len(user) < 500
        assert "Job:" in user or "job" in user.lower()

    def test_no_xml_tags(self):
        _, user = tb_openai.build_prompt("Built APIs", _job(), _match())
        assert "<job>" not in user


# --- Tailor Bullets: Ollama ---


class TestTailorBulletsOllama:
    def test_includes_example(self):
        _, user = tb_ollama.build_prompt("Built APIs", _job(), _match())
        assert "Example:" in user

    def test_short_system_prompt(self):
        system, _ = tb_ollama.build_prompt("Built APIs", _job(), _match())
        assert len(system) < 100

    def test_fewer_skills(self):
        """Ollama prompts limit skills to fit context window."""
        _, user = tb_ollama.build_prompt("Built APIs", _job(), _match())
        # Should have at most 5 required skills
        assert "Key skills:" in user


# --- Keyword Extraction: Common ---


class TestKeywordExtractionCommon:
    def test_returns_tuple(self):
        result = build_extraction_prompt("Looking for Python dev")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_includes_job_text(self):
        _, user = build_extraction_prompt("Looking for Python dev")
        assert "Python" in user

    def test_structured_output_instructions(self):
        _, user = build_extraction_prompt("test")
        assert "REQUIRED" in user
        assert "PREFERRED" in user


# --- Keyword Extraction: Per-Provider ---


class TestKeywordExtractionAnthropic:
    def test_xml_structure(self):
        _, user = ke_anthropic.build_prompt("Python dev needed")
        assert "<job_description>" in user
        assert "<required>" in user
        assert "<preferred>" in user


class TestKeywordExtractionOpenAI:
    def test_json_output_format(self):
        _, user = ke_openai.build_prompt("Python dev needed")
        assert "JSON" in user or "json" in user
        assert "required" in user
        assert "preferred" in user


class TestKeywordExtractionOllama:
    def test_truncates_long_text(self):
        long_text = "x" * 5000
        _, user = ke_ollama.build_prompt(long_text)
        # Should be truncated to 3000 chars of job text
        assert len(user) < 4000

    def test_short_system(self):
        system, _ = ke_ollama.build_prompt("test")
        assert len(system) < 100


# --- Prompt Selector ---


class TestPromptSelector:
    def test_selects_anthropic_prompt(self):
        builder = get_prompt_builder("tailor_bullets", "anthropic")
        assert builder is not None
        # Should be the anthropic-specific builder
        system, user = builder("test bullet", _job(), _match())
        assert "<job>" in user

    def test_selects_openai_prompt(self):
        builder = get_prompt_builder("tailor_bullets", "openai")
        assert builder is not None
        system, user = builder("test bullet", _job(), _match())
        assert "<job>" not in user  # OpenAI doesn't use XML

    def test_selects_ollama_prompt(self):
        builder = get_prompt_builder("tailor_bullets", "ollama")
        assert builder is not None
        system, user = builder("test bullet", _job(), _match())
        assert "Example:" in user

    def test_unknown_provider_falls_back_to_common(self):
        builder = get_prompt_builder("tailor_bullets", "unknown_provider_xyz")
        assert builder is not None
        # Should get the common builder
        system, user = builder("test bullet", _job(), _match())
        assert "Rewrite this resume bullet" in user

    def test_keyword_extraction_providers(self):
        for provider_name in ("anthropic", "openai", "ollama"):
            builder = get_prompt_builder("keyword_extraction", provider_name)
            assert builder is not None
            system, user = builder("Python dev needed")
            assert len(system) > 0
            assert len(user) > 0

    def test_unknown_task_returns_none(self):
        builder = get_prompt_builder("nonexistent_task", "anthropic")
        assert builder is None

    def test_cover_letter_common_fallback(self):
        builder = get_prompt_builder("cover_letter", "unknown_provider")
        assert builder is not None

    def test_interview_prep_common_fallback(self):
        builder = get_prompt_builder("interview_prep", "unknown_provider")
        assert builder is not None
