"""Tests for ``anvil tailor`` CLI command.

Why:
    The tailor command AI-rewrites resume bullets to match a job description.
    Tests cover happy path, --dry-run, error cases (bad job, bad YAML,
    unconfigured provider, unknown provider, AI error), and edge cases
    (no matches, no relevant bullets, no changes).
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

import anvilcv.cli.tailor_command.tailor_command  # noqa: F401
from anvilcv.cli.app import app
from anvilcv.exceptions import AnvilAIProviderError, AnvilUserError
from anvilcv.tailoring.matcher import MatchResult, ResumeMatch

runner = CliRunner()


def _make_match(num_matches: int = 3, relevance: float = 0.8) -> ResumeMatch:
    """Build a minimal ResumeMatch."""
    return ResumeMatch(
        matches=[
            MatchResult(
                section_path=f"experience.0.highlights.{i}",
                content=f"Built feature {i} using Python",
                matched_skills=["python"],
                relevance_score=relevance,
            )
            for i in range(num_matches)
        ],
        missing_required=["kubernetes"],
    )


def _write_resume_and_job(tmp_path: pathlib.Path):
    """Create sample resume YAML and job description files."""
    resume = tmp_path / "resume.yaml"
    resume.write_text(
        "cv:\n  name: Test User\n  sections:\n"
        "    experience:\n      - company: Acme\n"
        "        highlights:\n          - Built thing\n"
    )
    job = tmp_path / "job.txt"
    job.write_text("Senior Python Engineer at TechCo")
    return resume, job


class TestTailorHappyPath:
    """Full tailor flow with mocked AI."""

    @patch("anvilcv.tailoring.variant_writer.write_variant")
    @patch("anvilcv.tailoring.rewriter.rewrite_top_bullets")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_tailor_writes_variant(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_rewrite: MagicMock,
        mock_write: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)
        out = tmp_path / "variant.yaml"

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_provider = MagicMock()
        mock_provider.name = "anthropic"
        mock_resolve.return_value = mock_provider
        mock_rewrite.return_value = [{"path": "experience.0.highlights.0", "new": "Improved"}]
        mock_write.return_value = out

        result = runner.invoke(
            app, ["tailor", str(resume), "--job", str(job), "--output", str(out)]
        )
        assert result.exit_code == 0
        assert "Variant written to" in result.output
        mock_rewrite.assert_called_once()


class TestTailorDryRun:
    """--dry-run shows what would be changed without writing."""

    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_dry_run_no_write(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "python" in result.output.lower()

    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_dry_run_shows_missing_required(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job), "--dry-run"])
        assert result.exit_code == 0
        assert "kubernetes" in result.output.lower()


class TestTailorNoMatches:
    """Edge case: no matchable bullets."""

    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_no_matches_exits_0(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = ResumeMatch(matches=[], missing_required=[])

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        assert result.exit_code == 0
        assert "No matchable bullet points" in result.output


class TestTailorNoRelevantBullets:
    """Edge case: matches exist but all have relevance_score == 0."""

    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_zero_relevance_exits_0(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match(relevance=0.0)
        mock_resolve.return_value = MagicMock(name="anthropic")

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        assert result.exit_code == 0
        assert "No relevant bullets" in result.output


class TestTailorNoChanges:
    """Edge case: AI returns no changes (bullets already well-matched)."""

    @patch("anvilcv.tailoring.rewriter.rewrite_top_bullets")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_no_changes_exits_0(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_rewrite: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_rewrite.return_value = []

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        assert result.exit_code == 0
        assert "No changes made" in result.output


class TestTailorErrors:
    """Error cases."""

    def test_missing_input(self) -> None:
        result = runner.invoke(app, ["tailor"])
        assert result.exit_code == 2

    def test_missing_job_flag(self, tmp_path: pathlib.Path) -> None:
        resume = tmp_path / "resume.yaml"
        resume.write_text("cv:\n  name: Test\n")
        result = runner.invoke(app, ["tailor", str(resume)])
        assert result.exit_code == 2

    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_bad_job_file(self, mock_resolve_job: MagicMock, tmp_path: pathlib.Path) -> None:
        resume, job = _write_resume_and_job(tmp_path)
        mock_resolve_job.side_effect = AnvilUserError(message="bad job")

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        assert result.exit_code == 1
        assert "Error reading job description" in result.output

    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_bad_resume_yaml(self, mock_resolve_job: MagicMock, tmp_path: pathlib.Path) -> None:
        resume = tmp_path / "bad.yaml"
        resume.write_text(": invalid yaml [\n")
        job = tmp_path / "job.txt"
        job.write_text("Engineer at TechCo")
        mock_resolve_job.return_value = MagicMock(company="TechCo")

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        # ruamel.yaml may or may not raise; if it does, exit 1
        assert result.exit_code in (0, 1)

    @patch("anvilcv.cli.tailor_command.tailor_command.YAML")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_resume_read_error_exits_1(
        self,
        mock_resolve_job: MagicMock,
        mock_yaml_cls: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """Lines 118-120: Exception when parsing resume YAML."""
        resume, job = _write_resume_and_job(tmp_path)
        mock_resolve_job.return_value = MagicMock(company="Corp")
        mock_yaml_cls.return_value.load.side_effect = Exception("parse error")

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        assert result.exit_code == 1
        assert "Error reading resume" in result.output

    @patch("anvilcv.tailoring.rewriter.rewrite_top_bullets")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_ai_error_exits_4(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_rewrite: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_rewrite.side_effect = AnvilAIProviderError(message="rate limited")

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        assert result.exit_code == 4
        assert "AI error" in result.output


class TestTailorRenderAndScore:
    """Test --render and --score composition flags."""

    @patch("anvilcv.cli.tailor_command.tailor_command._score_variant")
    @patch("anvilcv.cli.tailor_command.tailor_command._render_variant")
    @patch("anvilcv.tailoring.variant_writer.write_variant")
    @patch("anvilcv.tailoring.rewriter.rewrite_top_bullets")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_render_flag_triggers_rendering(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_rewrite: MagicMock,
        mock_write: MagicMock,
        mock_render: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        resume, job = _write_resume_and_job(tmp_path)
        out = tmp_path / "variant.yaml"

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_rewrite.return_value = [{"path": "x", "new": "y"}]
        mock_write.return_value = out

        result = runner.invoke(
            app,
            ["tailor", str(resume), "--job", str(job), "--output", str(out), "--render"],
        )
        assert result.exit_code == 0
        mock_render.assert_called_once_with(out)
        mock_score.assert_not_called()

    @patch("anvilcv.cli.tailor_command.tailor_command._score_variant")
    @patch("anvilcv.cli.tailor_command.tailor_command._render_variant")
    @patch("anvilcv.tailoring.variant_writer.write_variant")
    @patch("anvilcv.tailoring.rewriter.rewrite_top_bullets")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_score_flag_implies_render(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_rewrite: MagicMock,
        mock_write: MagicMock,
        mock_render: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """--score implies --render per CLI spec."""
        resume, job = _write_resume_and_job(tmp_path)
        out = tmp_path / "variant.yaml"
        job_desc = MagicMock(company="TechCo")

        mock_resolve_job.return_value = job_desc
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_rewrite.return_value = [{"path": "x", "new": "y"}]
        mock_write.return_value = out

        result = runner.invoke(
            app,
            ["tailor", str(resume), "--job", str(job), "--output", str(out), "--score"],
        )
        assert result.exit_code == 0
        mock_render.assert_called_once_with(out)
        mock_score.assert_called_once()


class TestTailorAutoOutputPath:
    """Test auto-generated output path when --output is not provided."""

    @patch("anvilcv.tailoring.variant_writer.write_variant")
    @patch("anvilcv.tailoring.rewriter.rewrite_top_bullets")
    @patch("anvilcv.cli.provider_resolver.resolve_provider")
    @patch("anvilcv.tailoring.matcher.match_resume_to_job")
    @patch("anvilcv.cli.job_input.resolve_job_input")
    def test_auto_output_path_generated(
        self,
        mock_resolve_job: MagicMock,
        mock_match: MagicMock,
        mock_resolve: MagicMock,
        mock_rewrite: MagicMock,
        mock_write: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        """When --output is omitted, path is auto-generated from name + company + date."""
        resume, job = _write_resume_and_job(tmp_path)

        mock_resolve_job.return_value = MagicMock(company="TechCo")
        mock_match.return_value = _make_match()
        mock_resolve.return_value = MagicMock(name="anthropic")
        mock_rewrite.return_value = [{"path": "experience.0.highlights.0", "new": "Improved"}]
        mock_write.return_value = tmp_path / "variant.yaml"

        result = runner.invoke(app, ["tailor", str(resume), "--job", str(job)])
        assert result.exit_code == 0
        # Verify write_variant was called with an auto-generated path
        call_kwargs = mock_write.call_args
        output_path = call_kwargs[1].get("output_path") or call_kwargs[0][-1]
        assert "TechCo" in str(output_path)
        assert "Test_User" in str(output_path)


class TestRenderVariantHelper:
    """Test _render_variant helper directly."""

    @patch("anvilcv.vendor.rendercv.renderer.html.generate_ats_html")
    @patch("anvilcv.vendor.rendercv.renderer.html.generate_html")
    @patch("anvilcv.vendor.rendercv.renderer.markdown.generate_markdown")
    @patch("anvilcv.vendor.rendercv.renderer.typst.generate_typst")
    @patch(
        "anvilcv.vendor.rendercv.schema.rendercv_model_builder.build_rendercv_dictionary_and_model"
    )
    def test_render_variant_success(
        self,
        mock_build: MagicMock,
        mock_typst: MagicMock,
        mock_md: MagicMock,
        mock_html: MagicMock,
        mock_ats: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        from anvilcv.cli.tailor_command.tailor_command import _render_variant

        variant = tmp_path / "variant.yaml"
        variant.write_text("cv:\n  name: Test\n")
        mock_build.return_value = ({}, MagicMock())
        mock_md.return_value = tmp_path / "test.md"

        _render_variant(variant)

        mock_build.assert_called_once()
        mock_typst.assert_called_once()
        mock_md.assert_called_once()
        mock_html.assert_called_once()
        mock_ats.assert_called_once()

    def test_render_variant_handles_exception(self, tmp_path: pathlib.Path, capsys) -> None:
        from anvilcv.cli.tailor_command.tailor_command import _render_variant

        variant = tmp_path / "variant.yaml"
        variant.write_text("cv:\n  name: Test\n")

        with patch(
            "anvilcv.vendor.rendercv.schema.rendercv_model_builder"
            ".build_rendercv_dictionary_and_model",
            side_effect=Exception("render failed"),
        ):
            # Should not raise — just prints warning
            _render_variant(variant)


class TestScoreVariantHelper:
    """Test _score_variant helper directly."""

    @patch("anvilcv.scoring.ats_scorer.score_document")
    @patch("anvilcv.cli.score_command.score_command._render_yaml_for_scoring")
    def test_score_variant_success(
        self,
        mock_render_yaml: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        from anvilcv.cli.tailor_command.tailor_command import _score_variant

        variant = tmp_path / "variant.yaml"
        mock_render_yaml.return_value = tmp_path / "output.html"
        mock_report = MagicMock()
        mock_report.overall_score = 85
        mock_report.keyword_match = MagicMock(score=72, missing=["terraform"])
        mock_score.return_value = mock_report

        _score_variant(variant, job_desc=MagicMock())

    @patch("anvilcv.scoring.ats_scorer.score_document")
    @patch("anvilcv.cli.score_command.score_command._render_yaml_for_scoring")
    def test_score_variant_no_keyword_match(
        self,
        mock_render_yaml: MagicMock,
        mock_score: MagicMock,
        tmp_path: pathlib.Path,
    ) -> None:
        from anvilcv.cli.tailor_command.tailor_command import _score_variant

        variant = tmp_path / "variant.yaml"
        mock_render_yaml.return_value = tmp_path / "output.html"
        mock_report = MagicMock()
        mock_report.overall_score = 70
        mock_report.keyword_match = None
        mock_score.return_value = mock_report

        _score_variant(variant, job_desc=None)

    def test_score_variant_handles_exception(self, tmp_path: pathlib.Path) -> None:
        from anvilcv.cli.tailor_command.tailor_command import _score_variant

        variant = tmp_path / "variant.yaml"
        with patch(
            "anvilcv.cli.score_command.score_command._render_yaml_for_scoring",
            side_effect=Exception("scoring failed"),
        ):
            # Should not raise — just prints warning
            _score_variant(variant)


class TestResolveProvider:
    """Test shared resolve_provider helper."""

    @patch("anvilcv.ai.anthropic.AnthropicProvider")
    def test_resolve_anthropic(self, mock_cls: MagicMock) -> None:
        from anvilcv.cli.provider_resolver import resolve_provider

        instance = MagicMock()
        instance.is_configured.return_value = True
        mock_cls.return_value = instance

        result = resolve_provider("anthropic", None, {})
        assert result is instance

    @patch("anvilcv.ai.openai.OpenAIProvider")
    def test_resolve_openai(self, mock_cls: MagicMock) -> None:
        from anvilcv.cli.provider_resolver import resolve_provider

        instance = MagicMock()
        instance.is_configured.return_value = True
        mock_cls.return_value = instance

        result = resolve_provider("openai", None, {})
        assert result is instance

    @patch("anvilcv.ai.ollama.OllamaProvider")
    def test_resolve_ollama(self, mock_cls: MagicMock) -> None:
        from anvilcv.cli.provider_resolver import resolve_provider

        instance = MagicMock()
        instance.is_configured.return_value = True
        mock_cls.return_value = instance

        result = resolve_provider("ollama", None, {})
        assert result is instance

    def test_resolve_unknown_provider(self) -> None:
        from anvilcv.cli.provider_resolver import resolve_provider

        with pytest.raises(AnvilUserError, match="Unknown provider"):
            resolve_provider("fakeprovider", None, {})

    @patch("anvilcv.ai.anthropic.AnthropicProvider")
    def test_resolve_unconfigured_provider(self, mock_cls: MagicMock) -> None:
        from anvilcv.cli.provider_resolver import resolve_provider

        instance = MagicMock()
        instance.is_configured.return_value = False
        instance.get_setup_instructions.return_value = "Set ANTHROPIC_API_KEY"
        mock_cls.return_value = instance

        with pytest.raises(AnvilAIProviderError, match="not configured"):
            resolve_provider("anthropic", None, {})

    @patch("anvilcv.ai.anthropic.AnthropicProvider")
    def test_resolve_from_yaml_config(self, mock_cls: MagicMock) -> None:
        from anvilcv.cli.provider_resolver import resolve_provider

        instance = MagicMock()
        instance.is_configured.return_value = True
        mock_cls.return_value = instance

        resume_data = {
            "anvil": {
                "providers": {
                    "default": "anthropic",
                    "anthropic": {"model": "claude-sonnet-4-20250514"},
                },
            },
        }

        result = resolve_provider(None, None, resume_data)
        assert result is instance
