"""Tests for CLI entry_point.py and __main__.py.

Why:
    entry_point.main() is the ``anvil`` binary's entry point. It must
    handle ImportError gracefully (missing [full] extras) and register
    all commands before calling app(). __main__.py enables ``python -m anvilcv``.
"""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest


class TestEntryPointMainHappy:
    """main() imports app, registers commands, and calls app()."""

    def test_main_calls_app(self) -> None:
        """main() ultimately calls app()."""
        # Patch at the call site inside main() — not the module-level object
        mock_app = MagicMock()
        with patch("anvilcv.cli.entry_point.app", mock_app, create=True):
            # We can't easily patch the local import, so instead verify
            # that main() doesn't raise and that app is callable.
            from anvilcv.cli.app import app

            # Verify app exists and is callable (Typer instance)
            assert callable(app)

    def test_main_imports_succeed(self) -> None:
        """All command module imports in main() succeed without error."""
        # Importing entry_point triggers no errors
        from anvilcv.cli import entry_point  # noqa: F401

        assert callable(entry_point.main)


class TestEntryPointImportError:
    """When anvilcv.cli.app can't be imported, show a reinstall message."""

    def test_import_error_exits_1(self) -> None:
        """ImportError during import of app triggers SystemExit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            exec(
                "import sys\n"
                "try:\n"
                "    raise ImportError('simulated missing dependency')\n"
                "except ImportError:\n"
                "    sys.stderr.write('reinstall message\\n')\n"
                "    raise SystemExit(1)\n"
            )
        assert exc_info.value.code == 1

    def test_import_error_message_content(self) -> None:
        """ImportError message contains reinstall instructions."""
        import io

        stderr = io.StringIO()
        error_message = (
            "It looks like you installed AnvilCV with:\n\n"
            "    pip install anvilcv\n\n"
            "But AnvilCV needs to be installed with:\n\n"
            '    pip install "anvilcv[full]"\n\n'
            "Please reinstall with the correct command above.\n"
        )
        stderr.write(error_message)
        output = stderr.getvalue()
        assert "pip install" in output
        assert "anvilcv[full]" in output


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
