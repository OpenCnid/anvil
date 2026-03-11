"""Tests for prompt selector module.

Why:
    The selector dispatches to per-provider or common prompt builders.
    Tests cover the fallback path where common module import fails
    (_load_common_module returning None on ImportError).
"""

from __future__ import annotations

from unittest.mock import patch

from anvilcv.ai.prompts.selector import (
    _load_common_module,
    get_prompt_builder,
)


class TestLoadCommonModule:
    """Test _load_common_module, including import failure path."""

    def test_returns_none_for_unknown_task(self) -> None:
        result = _load_common_module("nonexistent_task")
        assert result is None

    def test_returns_none_when_import_fails(self) -> None:
        """Lines 45-46: ImportError causes _load_common_module to return None."""
        with patch(
            "anvilcv.ai.prompts.selector.importlib.import_module",
            side_effect=ImportError("no module"),
        ):
            result = _load_common_module("tailor_bullets")
            assert result is None

    def test_returns_none_when_module_not_found(self) -> None:
        with patch(
            "anvilcv.ai.prompts.selector.importlib.import_module",
            side_effect=ModuleNotFoundError("not found"),
        ):
            result = _load_common_module("cover_letter")
            assert result is None


class TestGetPromptBuilder:
    def test_returns_none_for_unknown_task(self) -> None:
        result = get_prompt_builder("totally_fake_task", "anthropic")
        assert result is None
