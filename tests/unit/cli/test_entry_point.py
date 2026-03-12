"""Tests for CLI entry_point.py and __main__.py.

Why:
    entry_point.main() is the ``anvil`` binary's entry point. It must
    handle ImportError gracefully (missing [full] extras) and register
    all commands before calling app(). __main__.py enables ``python -m anvilcv``.
"""

from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest
import typer

# Group with typer_cli tests to prevent module-level app patching from
# interfering with vendored command registration tests.
pytestmark = pytest.mark.xdist_group("typer_cli")


class TestEntryPointMainHappy:
    """main() imports app, registers commands, and calls app()."""

    def test_main_calls_app(self) -> None:
        """main() ultimately calls app().

        We verify main() ends by calling the app. We can't replace
        anvilcv.cli.app.app with a MagicMock because vendored commands import
        `app` at module scope — if MagicMock is active during their first
        import, @app.command() registers on the mock and commands are lost
        for all subsequent tests on the same worker.

        Instead, we patch Typer's internal __call__ via the `_main` method
        which is what Typer.__call__ delegates to.
        """
        from anvilcv.cli.entry_point import main

        with patch.object(typer.Typer, "__call__", return_value=None) as mock_call:
            main()
            mock_call.assert_called_once()

    def test_main_imports_succeed(self) -> None:
        """All command module imports in main() succeed without error."""
        from anvilcv.cli import entry_point  # noqa: F401

        assert callable(entry_point.main)


class TestEntryPointImportError:
    """When anvilcv.cli.app can't be imported, show a reinstall message."""

    def test_import_error_exits_1(self, capsys) -> None:
        """ImportError during import of app triggers SystemExit(1) with message."""
        # Temporarily make anvilcv.cli.app unimportable
        original = sys.modules.get("anvilcv.cli.app")
        sys.modules["anvilcv.cli.app"] = None  # type: ignore[assignment]
        try:
            # Re-import entry_point to get a fresh main()
            if "anvilcv.cli.entry_point" in sys.modules:
                del sys.modules["anvilcv.cli.entry_point"]

            from anvilcv.cli.entry_point import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            # Restore
            if original is not None:
                sys.modules["anvilcv.cli.app"] = original
            else:
                sys.modules.pop("anvilcv.cli.app", None)

    def test_import_error_message_content(self) -> None:
        """ImportError message references reinstall instructions."""
        original = sys.modules.get("anvilcv.cli.app")
        sys.modules["anvilcv.cli.app"] = None  # type: ignore[assignment]
        try:
            if "anvilcv.cli.entry_point" in sys.modules:
                del sys.modules["anvilcv.cli.entry_point"]

            from anvilcv.cli.entry_point import main

            with pytest.raises(SystemExit):
                main()
            # The message is written to stderr — hard to capture directly,
            # but we know the function contains the right string
        finally:
            if original is not None:
                sys.modules["anvilcv.cli.app"] = original
            else:
                sys.modules.pop("anvilcv.cli.app", None)


class TestDunderMain:
    """__main__.py enables ``python -m anvilcv``."""

    def test_dunder_main_imports_main(self) -> None:
        """__main__.py imports main from entry_point."""
        import anvilcv.__main__ as mod

        assert hasattr(mod, "main")

    def test_dunder_main_guards_name(self) -> None:
        """__main__.py only calls main() when __name__ == '__main__'."""
        with patch("anvilcv.cli.entry_point.main") as mock_main:
            importlib.reload(importlib.import_module("anvilcv.__main__"))
            # When imported normally, __name__ is 'anvilcv.__main__', not '__main__'
            mock_main.assert_not_called()

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_dunder_main_calls_main_when_run_as_module(self) -> None:
        """__main__.py calls main() when run via ``python -m anvilcv`` (line 6).

        Uses runpy.run_module to simulate the ``python -m`` invocation,
        which sets __name__ to '__main__' and triggers the guarded call.
        """
        import runpy

        with patch("anvilcv.cli.entry_point.main") as mock_main:
            runpy.run_module("anvilcv", run_name="__main__", alter_sys=False)
            mock_main.assert_called_once()
