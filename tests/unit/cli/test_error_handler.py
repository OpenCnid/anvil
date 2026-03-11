"""Tests for extended error handler — Anvil exception types with exit codes.

Why:
    The error handler must catch AnvilError subclasses (exit codes 1-4) and
    RenderCVUserError (exit code 1), displaying category-specific Rich panels.
    These tests verify correct exit codes and panel styling for each error type.
"""

from __future__ import annotations

import typer
from typer.testing import CliRunner

from anvilcv.exceptions import (
    AnvilAIProviderError,
    AnvilCLIError,
    AnvilServiceError,
    AnvilUserError,
)
from anvilcv.vendor.rendercv.cli.error_handler import handle_user_errors
from anvilcv.vendor.rendercv.exception import RenderCVUserError

runner = CliRunner()


def _make_app(error: Exception) -> typer.Typer:
    """Create a minimal Typer app that raises the given error."""
    app = typer.Typer()

    @app.command()
    @handle_user_errors
    def cmd() -> None:
        raise error

    return app


class TestAnvilErrorHandling:
    """Test that AnvilError subclasses produce correct exit codes."""

    def test_user_error_exit_code_1(self):
        app = _make_app(AnvilUserError(message="bad input"))
        result = runner.invoke(app)
        assert result.exit_code == 1

    def test_cli_error_exit_code_2(self):
        app = _make_app(AnvilCLIError(message="invalid flags"))
        result = runner.invoke(app)
        assert result.exit_code == 2

    def test_service_error_exit_code_3(self):
        app = _make_app(AnvilServiceError(message="GitHub API down"))
        result = runner.invoke(app)
        assert result.exit_code == 3

    def test_ai_provider_error_exit_code_4(self):
        app = _make_app(AnvilAIProviderError(message="rate limited"))
        result = runner.invoke(app)
        assert result.exit_code == 4

    def test_user_error_shows_message(self):
        app = _make_app(AnvilUserError(message="file not found"))
        result = runner.invoke(app)
        assert "file not found" in result.output

    def test_service_error_shows_message(self):
        app = _make_app(AnvilServiceError(message="GitHub API timeout"))
        result = runner.invoke(app)
        assert "GitHub API timeout" in result.output

    def test_ai_error_shows_message(self):
        app = _make_app(AnvilAIProviderError(message="context overflow"))
        result = runner.invoke(app)
        assert "context overflow" in result.output


class TestRenderCVErrorHandling:
    """Test that vendored RenderCVUserError still works."""

    def test_rendercv_error_exit_code_1(self):
        app = _make_app(RenderCVUserError(message="invalid YAML"))
        result = runner.invoke(app)
        assert result.exit_code == 1

    def test_rendercv_error_shows_message(self):
        app = _make_app(RenderCVUserError(message="missing field"))
        result = runner.invoke(app)
        assert "missing field" in result.output


class TestErrorPrecedence:
    """Test that AnvilError is caught before RenderCVUserError."""

    def test_anvil_error_caught_first(self):
        """AnvilError handler runs before RenderCVUserError handler."""
        app = _make_app(AnvilServiceError(message="test precedence"))
        result = runner.invoke(app)
        # Service errors get exit code 3, not 1
        assert result.exit_code == 3
