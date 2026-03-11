"""Entry point for the ``anvil`` CLI binary.

Why:
    Mirrors rendercv's dependency-safe pattern: if the user installed
    ``pip install anvilcv`` without ``[full]`` extras, catch the ImportError
    early and show a helpful reinstall message instead of a confusing traceback.

    The pyproject.toml ``[project.scripts]`` entry points here::

        anvil = "anvilcv.cli.entry_point:main"
"""

import sys


def main() -> None:
    """Entry point for the ``anvil`` CLI command."""
    try:
        from anvilcv.cli.app import app  # noqa: PLC0415
    except ImportError:
        error_message = """
It looks like you installed AnvilCV with:

    pip install anvilcv

But AnvilCV needs to be installed with:

    pip install "anvilcv[full]"

Please reinstall with the correct command above.
"""
        sys.stderr.write(error_message)
        raise SystemExit(1) from None

    # Trigger vendored rendercv command registration (render, new, create_theme)
    import anvilcv.vendor.rendercv.cli.app  # noqa: F401, PLC0415

    app()
